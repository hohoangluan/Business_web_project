"""
Views cho hồ sơ cá nhân và quản lý hồ sơ nhân sự (HR/Admin).
"""

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User

from accounts.models import UserProfile, Role
from accounts.services import (
    ensure_profile, ensure_work_info, ensure_contract_info,
    is_admin_user, is_hr_user, can_manage_work_info,
)
from employee_profiles.forms import EmployeeProfileForm
from employee_profiles.services import (
    get_manager_user_queryset, get_leader_user_queryset,
    build_hr_create_profile_context,
    save_work_info_from_data, save_contract_info_from_data,
)


@login_required
def profile_view(request):
    """
    Trang hồ sơ cá nhân.
    - GET: hiển thị thông tin
    - POST: cập nhật thông tin cá nhân cơ bản
    Template: employee_profiles/profile.html
    """
    profile = ensure_profile(request.user)
    ensure_work_info(request.user)
    ensure_contract_info(request.user)

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        date_of_birth = request.POST.get('date_of_birth', '').strip()

        if full_name:
            profile.full_name = full_name
        if email:
            request.user.email = email
            request.user.save()
        if phone_number:
            profile.phone_number = phone_number
        if date_of_birth:
            profile.date_of_birth = date_of_birth

        profile.save()
        messages.success(request, 'Cập nhật hồ sơ thành công!')
        return redirect('profile')

    return render(request, 'employee_profiles/profile.html', {
        'active_page': 'profile',
    })


@login_required
@user_passes_test(is_hr_user)
def hr_create_profile_view(request):
    """
    HR tạo hồ sơ nhân viên mới.
    - GET: hiển thị form
    - POST: tạo User + UserProfile + EmployeeWorkInfo + ContractInfo
    Template: employee_profiles/hr_create_profile.html
    """
    ensure_profile(request.user)

    if request.method == 'POST':
        # Đọc dữ liệu từ form
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone_number', '').strip()
        dob = request.POST.get('date_of_birth', '').strip()
        employee_id = request.POST.get('employee_id', '').strip()
        employee_type = request.POST.get('employee_type', '').strip()
        department = request.POST.get('department', '').strip()
        position = request.POST.get('position', '').strip()
        workplace = request.POST.get('workplace', '').strip()
        probation_start = request.POST.get('probation_start', '').strip()
        official_start_date = request.POST.get('official_start_date', '').strip()
        contract_number = request.POST.get('contract_number', '').strip()
        contract_type = request.POST.get('contract_type', '').strip()
        contract_signed_date = request.POST.get('contract_signed_date', '').strip()
        contract_start_date = request.POST.get('contract_start_date', '').strip()
        contract_end_date = request.POST.get('contract_end_date', '').strip()
        contract_annual_leave_days_raw = request.POST.get('contract_annual_leave_days', '').strip()
        contract_standard_shift = request.POST.get('contract_standard_shift', '').strip()
        contract_attachment_reference = request.POST.get('contract_attachment_reference', '').strip()
        work_status = request.POST.get('work_status', '').strip()
        manager_user_id = request.POST.get('manager_user', '').strip()
        leader_user_id = request.POST.get('leader_user', '').strip()
        role_name = request.POST.get('role', '').strip()
        auto_create = request.POST.get('auto_create_account') == 'on'

        manager_user = User.objects.filter(pk=manager_user_id).first() if manager_user_id else None
        leader_user = User.objects.filter(pk=leader_user_id).first() if leader_user_id else None
        contract_annual_leave_days = None

        # Validation
        errors = []
        if not employee_id:
            errors.append('Mã nhân viên không được để trống.')
        elif UserProfile.objects.filter(employee_id=employee_id).exists():
            errors.append(f'Mã nhân viên "{employee_id}" đã tồn tại.')
        if not department:
            errors.append('Phòng ban không được để trống.')
        if not position:
            errors.append('Chức vụ không được để trống.')
        if not employee_type:
            errors.append('Loại nhân viên không được để trống.')
        if not workplace:
            errors.append('Nơi làm việc không được để trống.')
        if not probation_start:
            errors.append('Ngày bắt đầu thử việc không được để trống.')
        if not official_start_date:
            errors.append('Ngày làm việc chính thức không được để trống.')
        if not work_status:
            errors.append('Trạng thái làm việc không được để trống.')
        if not manager_user:
            errors.append('Cần gán quản lý trực tiếp.')
        if not leader_user:
            errors.append('Cần gán leader phụ trách.')
        if not contract_number:
            errors.append('Số hợp đồng không được để trống.')
        if not contract_type:
            errors.append('Loại hợp đồng không được để trống.')
        if not contract_signed_date:
            errors.append('Ngày ký hợp đồng không được để trống.')
        if not contract_start_date:
            errors.append('Ngày bắt đầu hiệu lực không được để trống.')
        if not contract_annual_leave_days_raw:
            errors.append('Số ngày nghỉ phép/năm không được để trống.')
        else:
            try:
                contract_annual_leave_days = int(contract_annual_leave_days_raw)
                if contract_annual_leave_days < 0:
                    errors.append('Số ngày nghỉ phép/năm phải từ 0 trở lên.')
            except ValueError:
                errors.append('Số ngày nghỉ phép/năm phải là số nguyên.')
        if not contract_standard_shift:
            errors.append('Ca làm tiêu chuẩn không được để trống.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(
                request,
                'employee_profiles/hr_create_profile.html',
                build_hr_create_profile_context(request.POST),
            )

        if auto_create:
            username = employee_id.lower().replace(' ', '')
            password = f'{employee_id}@2026'

            if User.objects.filter(username=username).exists():
                messages.error(request, f'Username "{username}" đã tồn tại.')
                return render(
                    request,
                    'employee_profiles/hr_create_profile.html',
                    build_hr_create_profile_context(request.POST),
                )

            # Tạo User + Profile
            user = User.objects.create_user(username=username, email=email, password=password)
            profile = ensure_profile(user)
            profile.full_name = full_name
            profile.phone_number = phone
            profile.date_of_birth = dob
            profile.employee_id = employee_id
            if role_name:
                role, _ = Role.objects.get_or_create(name=role_name)
                profile.role = role
            profile.save()

            # Lưu thông tin công việc
            save_work_info_from_data(user, {
                'employee_type': employee_type,
                'department': department,
                'position': position,
                'workplace': workplace,
                'probation_start': probation_start,
                'official_start_date': official_start_date,
                'work_status': work_status,
                'manager_user': manager_user,
                'leader_user': leader_user,
            })

            # Lưu thông tin hợp đồng
            save_contract_info_from_data(user, {
                'contract_number': contract_number,
                'contract_type': contract_type,
                'contract_signed_date': contract_signed_date,
                'contract_start_date': contract_start_date,
                'contract_end_date': contract_end_date,
                'contract_annual_leave_days': contract_annual_leave_days,
                'contract_standard_shift': contract_standard_shift,
                'contract_attachment_reference': contract_attachment_reference,
            })

            display_name = full_name or employee_id
            messages.success(
                request,
                f'✅ Đã tạo hồ sơ và tài khoản cho "{display_name}"! '
                f'Username: {username} | Mật khẩu: {password}'
            )
        else:
            display_name = full_name or employee_id or 'nhân viên mới'
            messages.success(
                request,
                f'✅ Đã mô phỏng lưu hồ sơ "{display_name}". Demo UI.'
            )

        return redirect('hr_create_profile')

    return render(
        request,
        'employee_profiles/hr_create_profile.html',
        build_hr_create_profile_context(),
    )


@login_required
@user_passes_test(can_manage_work_info)
def edit_work_info_view(request, user_id):
    """
    HR/Admin chỉnh toàn bộ hồ sơ nhân viên.
    Template: employee_profiles/edit_work_info.html
    """
    target_user = get_object_or_404(User, pk=user_id)
    profile = ensure_profile(target_user)
    work_info = ensure_work_info(target_user)
    contract_info = ensure_contract_info(target_user)

    manager_queryset = get_manager_user_queryset()
    leader_queryset = get_leader_user_queryset()

    if request.method == 'POST':
        form = EmployeeProfileForm(
            request.POST,
            manager_queryset=manager_queryset,
            leader_queryset=leader_queryset,
            current_user=target_user,
        )
        if form.is_valid():
            # Lưu thông tin cá nhân vào UserProfile
            target_user.email = form.cleaned_data['email']
            target_user.save()
            profile.full_name = form.cleaned_data['full_name']
            profile.phone_number = form.cleaned_data['phone_number']
            profile.date_of_birth = form.cleaned_data['date_of_birth']
            profile.employee_id = form.cleaned_data['employee_id']
            profile.save()

            # Lưu thông tin công việc vào EmployeeWorkInfo
            save_work_info_from_data(target_user, form.cleaned_data)

            # Lưu thông tin hợp đồng vào ContractInfo
            save_contract_info_from_data(target_user, form.cleaned_data)

            messages.success(request, f'Đã cập nhật hồ sơ nhân sự cho "{target_user.username}".')
            return redirect('user_list')
    else:
        form = EmployeeProfileForm(
            initial={
                'full_name': profile.full_name,
                'email': target_user.email,
                'phone_number': profile.phone_number,
                'date_of_birth': profile.date_of_birth,
                'employee_id': profile.employee_id,
                'department': work_info.department,
                'employee_type': work_info.employee_type,
                'position': work_info.position,
                'workplace': work_info.workplace,
                'probation_start': work_info.probation_start,
                'official_start_date': work_info.official_start_date,
                'work_status': work_info.work_status,
                'manager_user': work_info.manager_user,
                'leader_user': work_info.leader_user,
                'contract_number': contract_info.contract_number,
                'contract_type': contract_info.contract_type,
                'contract_signed_date': contract_info.contract_signed_date,
                'contract_start_date': contract_info.contract_start_date,
                'contract_end_date': contract_info.contract_end_date,
                'contract_annual_leave_days': contract_info.contract_annual_leave_days,
                'contract_standard_shift': contract_info.contract_standard_shift,
                'contract_attachment_reference': contract_info.contract_attachment_reference,
            },
            manager_queryset=manager_queryset,
            leader_queryset=leader_queryset,
            current_user=target_user,
        )

    return render(request, 'employee_profiles/edit_work_info.html', {
        'form': form,
        'target_user': target_user,
        'active_page': 'users',
        'can_manage_system_users': is_admin_user(request.user),
    })
