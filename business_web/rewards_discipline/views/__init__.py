"""Views cho khen thưởng & xử phạt."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from accounts.services import (
    ensure_profile,
    is_hr_user,
    can_manage_requests,
    user_has_role,
)
from accounts.models import Role
from accounts.services import is_admin_user, user_has_role
from rewards_discipline.models import RewardPenalty
from rewards_discipline.forms import RewardPenaltyForm
from rewards_discipline.services import (
    approve_reward_penalty,
    get_pending_for_approver,
    initial_status_for,
    reject_reward_penalty,
)


@login_required
def rewards_penalties_view(request):
    """Trang khen thưởng & xử phạt cá nhân hoặc lọc theo nhân viên đối với HR."""
    ensure_profile(request.user)

    if getattr(request.user.profile.role, 'name', None) == 'employee' or is_admin_user(request.user):
        messages.error(request, 'Tài khoản của bạn không có quyền truy cập chức năng Khen thưởng & Xử phạt.')
        return redirect('dashboard')

    # 1. Xác định vai trò HR / Admin (dùng service an toàn)
    is_hr = is_hr_user(request.user)

    # 2. Xử lý lựa chọn nhân viên để xem (chỉ áp dụng đối với HR)
    all_employees = []
    if is_hr:
        # HR xem được phiếu của TẤT CẢ nhân viên (mọi staff), chỉ loại tài khoản Admin
        # hệ thống — Admin không phải nhân viên, không có khen thưởng/xử phạt.
        all_employees = (
            User.objects.filter(is_active=True)
            .exclude(profile__role__name=Role.ADMIN)
            .exclude(is_superuser=True)
            .select_related('profile').order_by('username')
        )
        target_user_id = request.GET.get('employee_id')
        if target_user_id:
            selected_user = get_object_or_404(User, id=target_user_id)
            if is_admin_user(selected_user):
                messages.error(request, 'Tài khoản Admin không có khen thưởng/xử phạt.')
                selected_user = request.user
        else:
            selected_user = request.user
    else:
        selected_user = request.user

    # 3. Lấy danh sách phiếu thưởng/phạt của nhân viên đang được xem
    records = RewardPenalty.objects.filter(employee=selected_user).order_by('-application_date')

    rewards = []
    penalties = []
    total_reward = 0
    total_penalty = 0

    for r in records:
        prefix = "+" if r.record_type == 'reward' else "-"
        r.amount_formatted = f"{prefix} {r.amount:,}đ".replace(',', '.')

        if r.record_type == 'reward':
            rewards.append(r)
            if r.status == 'approved':
                total_reward += r.amount
        elif r.record_type == 'penalty':
            penalties.append(r)
            if r.status == 'approved':
                total_penalty += r.amount

    net_income = total_reward - total_penalty

    # Định dạng các stats cards tổng hợp
    total_reward_formatted = f"+ {total_reward:,}đ".replace(',', '.')
    total_penalty_formatted = f"- {total_penalty:,}đ".replace(',', '.')
    net_prefix = "+" if net_income >= 0 else "-"
    net_income_formatted = f"{net_prefix} {abs(net_income):,}đ".replace(',', '.')

    # 4. Kiểm tra quyền đề xuất tạo phiếu mới (chỉ Leader / Manager / HR / Admin)
    can_propose = can_manage_requests(request.user)

    form = None
    if can_propose:
        if request.method == 'POST' and request.POST.get('action') == 'create':
            form = RewardPenaltyForm(request.POST, request.FILES, user=request.user)
            if form.is_valid():
                instance = form.save(commit=False)
                instance.proposer = request.user
                instance.status = initial_status_for(request.user)
                instance.save()
                messages.success(request, 'Tạo đề xuất Khen thưởng / Xử phạt thành công! Phiếu đã được gửi tới phòng Nhân sự chờ duyệt.')
                return redirect('rewards_penalties')
            else:
                messages.error(request, 'Có lỗi xảy ra, vui lòng kiểm tra lại thông tin biểu mẫu.')
        else:
            form = RewardPenaltyForm(user=request.user)

    return render(request, 'rewards_discipline/rewards_penalties.html', {
        'active_page': 'rewards',
        'is_hr': is_hr,
        'can_propose': can_propose,
        'selected_user': selected_user,
        'all_employees': all_employees,
        'rewards': rewards,
        'penalties': penalties,
        'total_reward_formatted': total_reward_formatted,
        'total_penalty_formatted': total_penalty_formatted,
        'net_income_formatted': net_income_formatted,
        'form': form,
    })


@login_required
def rewards_penalties_approval_view(request):
    """Trang phê duyệt thưởng/phạt — duyệt 2 cấp.

    Manager xử lý cấp 1 (phiếu Leader lập, status=pending);
    HR/Admin xử lý cấp 2 (status=leader_approved).
    """
    ensure_profile(request.user)

    # 1. Bảo mật: Manager (L1) hoặc HR/Admin (L2) mới được duyệt.
    is_approver = (
        user_has_role(request.user, Role.MANAGER)
        or is_hr_user(request.user)
        or is_admin_user(request.user)
    )
    if not is_approver:
        messages.error(request, 'Bạn không có quyền truy cập trang phê duyệt Thưởng / Phạt.')
        return redirect('rewards_penalties')

    # 2. Xử lý POST duyệt / từ chối — định tuyến theo cấp trong service.
    if request.method == 'POST':
        action = request.POST.get('action')
        record_id = request.POST.get('record_id')
        if action == 'approve':
            success, msg = approve_reward_penalty(request.user, record_id)
        elif action == 'reject':
            success, msg = reject_reward_penalty(request.user, record_id)
        else:
            success, msg = False, 'Hành động không hợp lệ.'
        (messages.success if success else messages.error)(request, msg)
        return redirect('rewards_penalties_approval')

    # 3. Hàng đợi theo vai trò người duyệt.
    pending_records = get_pending_for_approver(request.user)

    for r in pending_records:
        prefix = "+" if r.record_type == 'reward' else "-"
        r.amount_formatted = f"{prefix} {r.amount:,}đ".replace(',', '.')

    return render(request, 'rewards_discipline/rewards_penalties_approval.html', {
        'active_page': 'rewards',
        'pending_records': pending_records,
    })
