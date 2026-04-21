"""
==============================================================================
ACCOUNTS VIEWS - accounts/views.py
==============================================================================
File này xử lý tất cả logic backend cho module tài khoản.
Mỗi view function nhận request từ URL → xử lý logic → trả về template.

VIEWS HIỆN CÓ (giữ nguyên logic, chỉ cập nhật template context):
  - register_view: Đăng ký tài khoản
  - dashboard_view: Trang chủ sau đăng nhập
  - logout_view: Đăng xuất
  - user_list_view: Danh sách tài khoản (NÂNG CẤP)
  - assign_role_view: Gán vai trò
  - assign_permissions_view: Gán quyền
  - delete_user_view: Xóa tài khoản

VIEWS MỚI:
  - profile_view: Xem/chỉnh sửa hồ sơ cá nhân
  - toggle_user_active_view: Khóa/mở khóa tài khoản
  - reset_user_password_view: Reset mật khẩu tài khoản
==============================================================================
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import RegisterForm, AssignRoleForm, AssignPermissionsForm
from .models import UserProfile


# =============================================================================
# HELPER: Access Control Check
# =============================================================================

def is_admin_user(user):
    """
    Kiểm tra user có quyền quản trị không.
    Trả về True nếu user là superuser HOẶC có role 'Admin'.

    Hàm này dùng với @user_passes_test decorator:
      - True → user được truy cập trang
      - False → user bị redirect về trang login
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        return user.profile.is_admin()
    except UserProfile.DoesNotExist:
        return False


def ensure_profile(user):
    """
    Đảm bảo user có UserProfile.
    Nếu chưa có (VD: user tạo trước khi có profile system), tự động tạo.
    """
    profile, created = UserProfile.objects.get_or_create(user=user)
    return profile


# =============================================================================
# PUBLIC VIEWS: Registration, Login, Logout, Dashboard
# =============================================================================

def register_view(request):
    """
    Xử lý đăng ký tài khoản với 7 trường.
    - GET: hiển thị form đăng ký
    - POST: validate, tạo user + profile, tự động đăng nhập

    Template: accounts/register.html
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()           # Lưu user (username, email, password)

            # Tạo UserProfile với các trường đăng ký bổ sung
            profile = ensure_profile(user)
            profile.full_name = form.cleaned_data['full_name']
            profile.phone_number = form.cleaned_data['phone_number']
            profile.date_of_birth = form.cleaned_data['date_of_birth']
            profile.employee_id = form.cleaned_data['employee_id']
            profile.save()

            login(request, user)         # Tự động đăng nhập sau đăng ký
            messages.success(request, 'Đăng ký tài khoản thành công! Chào mừng bạn.')
            return redirect('dashboard')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def dashboard_view(request):
    """
    Trang chủ sau khi đăng nhập.
    Hiển thị thông tin tổng quan, link điều hướng theo vai trò.

    Template: accounts/dashboard.html
    Context: active_page - để sidebar highlight đúng menu item
    """
    ensure_profile(request.user)
    return render(request, 'accounts/dashboard.html', {
        'active_page': 'dashboard',  # Sidebar highlight
    })


def logout_view(request):
    """Đăng xuất và redirect về trang đăng nhập."""
    logout(request)
    messages.info(request, 'Bạn đã đăng xuất thành công.')
    return redirect('login')


# =============================================================================
# PROFILE VIEW (MỚI)
# =============================================================================

@login_required
def profile_view(request):
    """
    Trang hồ sơ cá nhân.
    - GET: Hiển thị thông tin user hiện tại
    - POST: Cập nhật các trường cho phép chỉnh sửa

    Các trường CÓ THỂ chỉnh sửa (đã có trong model):
      - full_name, email, phone_number, date_of_birth

    Các trường khác (giới tính, CCCD, phòng ban, ngân hàng...)
    CHƯA CÓ trong model → hiển thị mock data trên template.
    → Khi thêm field vào model, chỉ cần thêm vào form xử lý bên dưới.

    Template: accounts/profile.html
    """
    profile = ensure_profile(request.user)

    if request.method == 'POST':
        # Cập nhật các field có trong model
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        date_of_birth = request.POST.get('date_of_birth', '').strip()

        # Validate đơn giản
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

    ensure_profile(request.user)
    return render(request, 'accounts/profile.html', {
        'active_page': 'profile'
    })


@login_required
def contract_view(request):
    """
    Trang giao diện Hợp đồng lao động. MOCK DATA.
    - HR có quyền được hiển thị nút Tạo/Sửa.
    """
    ensure_profile(request.user)
    role_name = request.user.profile.role.name if request.user.profile.role else ''
    is_hr = role_name == 'hr'
    
    # Cảnh báo: mọi role TRỪ admin
    show_warning = not is_admin_user(request.user)

    return render(request, 'accounts/contract.html', {
        'active_page': 'contract',
        'is_hr': is_hr,
        'show_warning': show_warning,
    })


@login_required
def attendance_view(request):
    """
    Trang giao diện Chấm công. MOCK DATA.
    - Hiển thị đồng hồ thời gian thực và lịch sử điểm danh.
    """
    ensure_profile(request.user)
    return render(request, 'accounts/attendance.html', {
        'active_page': 'attendance',
    })


@login_required
def leave_view(request):
    """
    Trang giao diện Nghỉ phép cá nhân. MOCK DATA.
    - Hiển thị danh sách nghỉ phép của chính mình.
    - Hiển thị nút Phê duyệt nếu user có quyền.
    """
    ensure_profile(request.user)
    
    # Kiểm tra quyền duyệt nghỉ phép (HR, Manager, Leader, Admin)
    can_approve = False
    if request.user.is_superuser or is_admin_user(request.user):
        can_approve = True
    elif hasattr(request.user, 'role') and request.user.role:
        if request.user.role.name in ['HR', 'Manager', 'Leader']:
            can_approve = True
            
    return render(request, 'accounts/leave.html', {
        'active_page': 'leave',
        'can_approve': can_approve,
    })


@login_required
def leave_approval_view(request):
    """
    Trang giao diện Phê duyệt Nghỉ phép. MOCK DATA.
    - Chỉ dành cho HR, Manager, Leader, Admin.
    """
    ensure_profile(request.user)
    
    # Kiểm tra lại quyền truy cập trang này
    can_approve = False
    if request.user.is_superuser or is_admin_user(request.user):
        can_approve = True
    elif hasattr(request.user, 'role') and request.user.role:
        if request.user.role.name in ['HR', 'Manager', 'Leader']:
            can_approve = True
            
    if not can_approve:
        messages.error(request, 'Bạn không có quyền truy cập trang phê duyệt!')
        return redirect('leave')
        
    return render(request, 'accounts/leave_approval.html', {
        'active_page': 'leave',  # giữ sidebar highlight ở phần mục Nghỉ phép
    })


@login_required
def overtime_view(request):
    """
    Trang giao diện Tăng ca cá nhân. MOCK DATA.
    - Hiển thị danh sách overtime của chính mình và biểu đồ tĩnh.
    - Hiển thị nút Phê duyệt nếu user có quyền.
    """
    ensure_profile(request.user)
    
    can_approve = False
    if request.user.is_superuser or is_admin_user(request.user):
        can_approve = True
    elif hasattr(request.user, 'role') and request.user.role:
        if request.user.role.name in ['HR', 'Manager', 'Leader']:
            can_approve = True
            
    return render(request, 'accounts/overtime.html', {
        'active_page': 'overtime',
        'can_approve': can_approve,
    })


@login_required
def overtime_approval_view(request):
    """
    Trang giao diện Phê duyệt Tăng ca. MOCK DATA.
    """
    ensure_profile(request.user)
    
    can_approve = False
    if request.user.is_superuser or is_admin_user(request.user):
        can_approve = True
    elif hasattr(request.user, 'role') and request.user.role:
        if request.user.role.name in ['HR', 'Manager', 'Leader']:
            can_approve = True
            
    if not can_approve:
        messages.error(request, 'Bạn không có quyền truy cập trang phê duyệt!')
        return redirect('overtime')
        
    return render(request, 'accounts/overtime_approval.html', {
        'active_page': 'overtime', 
    })


@login_required
def statistics_view(request):
    """
    Trang Thống kê quản trị (Biểu đồ).
    MOCK DATA.
    """
    ensure_profile(request.user)
    return render(request, 'accounts/statistics.html', {
        'active_page': 'statistics',
    })

@login_required
def report_view(request):
    """
    Trang Báo cáo cá nhân.
    - Hiển thị báo cáo tự tạo.
    - Nút truy cập Hộp thư dành cho quản lý.
    """
    ensure_profile(request.user)
    
    is_manager = False
    if request.user.is_superuser or is_admin_user(request.user):
        is_manager = True
    elif hasattr(request.user, 'role') and request.user.role:
        if request.user.role.name in ['HR', 'Manager', 'Leader']:
            is_manager = True
            
    return render(request, 'accounts/report.html', {
        'active_page': 'reports',
        'is_manager': is_manager,
    })

@login_required
def report_inbox_view(request):
    """
    Hộp thư nhận báo cáo từ nhân viên.
    Chỉ cho phép Manager, HR, Leader, Admin.
    """
    ensure_profile(request.user)
    
    is_manager = False
    if request.user.is_superuser or is_admin_user(request.user):
        is_manager = True
    elif hasattr(request.user, 'role') and request.user.role:
        if request.user.role.name in ['HR', 'Manager', 'Leader']:
            is_manager = True
            
    if not is_manager:
        messages.error(request, 'Bạn không có quyền xem hộp thư báo cáo!')
        return redirect('reports')
        
    return render(request, 'accounts/report_inbox.html', {
        'active_page': 'reports', 
    })


@login_required
def ticket_list_view(request):
    """
    Trang Quản lý Hỗ trợ & Khiếu nại cá nhân.
    - Hiển thị danh sách ticket của chính mình.
    - Nút xử lý nếu user có quyền Manager/HR.
    """
    ensure_profile(request.user)
    
    can_process = False
    if request.user.is_superuser or is_admin_user(request.user):
        can_process = True
    elif hasattr(request.user, 'role') and request.user.role:
        if request.user.role.name in ['HR', 'Manager', 'Leader']:
            can_process = True
            
    return render(request, 'accounts/tickets.html', {
        'active_page': 'tickets',
        'can_process': can_process,
    })

@login_required
def ticket_process_view(request):
    """
    Trang Xử lý Hỗ trợ & Khiếu nại (Quản lý).
    """
    ensure_profile(request.user)
    
    can_process = False
    if request.user.is_superuser or is_admin_user(request.user):
        can_process = True
    elif hasattr(request.user, 'role') and request.user.role:
        if request.user.role.name in ['HR', 'Manager', 'Leader']:
            can_process = True
            
    if not can_process:
        messages.error(request, 'Bạn không có quyền truy cập trang xử lý ticket!')
        return redirect('tickets')
        
    return render(request, 'accounts/ticket_process.html', {
        'active_page': 'tickets', 
    })


@login_required
def rewards_penalties_view(request):
    """
    Trang Quản lý Khen thưởng & Xử phạt cá nhân.
    - Nút đến trang phê duyệt nếu user có quyền Manager/HR/Admin.
    """
    ensure_profile(request.user)
    
    can_approve = False
    if request.user.is_superuser or is_admin_user(request.user):
        can_approve = True
    elif hasattr(request.user, 'role') and request.user.role:
        if request.user.role.name in ['HR', 'Manager', 'Leader']:
            can_approve = True
            
    return render(request, 'accounts/rewards_penalties.html', {
        'active_page': 'rewards',
        'can_approve': can_approve,
    })

@login_required
def rewards_penalties_approval_view(request):
    """
    Trang Phê duyệt Khen thưởng & Xử phạt.
    """
    ensure_profile(request.user)
    
    can_approve = False
    if request.user.is_superuser or is_admin_user(request.user):
        can_approve = True
    elif hasattr(request.user, 'role') and request.user.role:
        if request.user.role.name in ['HR', 'Manager', 'Leader']:
            can_approve = True
            
    if not can_approve:
        messages.error(request, 'Bạn không có quyền truy cập trang phê duyệt!')
        return redirect('rewards_penalties')
        
    return render(request, 'accounts/rewards_penalties_approval.html', {
        'active_page': 'rewards', 
    })


@login_required
def payroll_view(request):
    """
    Trang Tiền lương / Phiếu lương cá nhân (Payslip).
    """
    ensure_profile(request.user)
    
    is_hr = False
    is_director = False
    
    if request.user.is_superuser or is_admin_user(request.user):
        is_hr = True
        is_director = True
    elif hasattr(request.user, 'role') and request.user.role:
        if request.user.role.name in ['HR']:
            is_hr = True
        elif request.user.role.name in ['Manager', 'Leader']:
            # Trong thực tế, Manager có thể xem tổng quan lương phòng ban, Giám đốc mới được duyệt.
            is_director = True 
            
    return render(request, 'accounts/payroll.html', {
        'active_page': 'payroll',
        'is_hr': is_hr,
        'is_director': is_director,
    })

@login_required
def payroll_calc_view(request):
    """
    Trang Tính lương tự động (Dành cho HR/Kế toán).
    """
    ensure_profile(request.user)
    
    is_hr = False
    if request.user.is_superuser or is_admin_user(request.user):
        is_hr = True
    elif hasattr(request.user, 'role') and request.user.role:
        if request.user.role.name in ['HR']:
            is_hr = True
            
    if not is_hr:
        messages.error(request, 'Chỉ bộ phận HR/Kế toán mới được truy cập công cụ tính lương!')
        return redirect('payroll')
        
    return render(request, 'accounts/payroll_calc.html', {
        'active_page': 'payroll', 
    })

@login_required
def payroll_approval_view(request):
    """
    Trang Phê duyệt Bảng lương Tổng (Dành cho Manager/Giám đốc).
    """
    ensure_profile(request.user)
    
    is_director = False
    if request.user.is_superuser or is_admin_user(request.user):
        is_director = True
    elif hasattr(request.user, 'role') and request.user.role:
        if request.user.role.name in ['Manager', 'Leader']:
            is_director = True
            
    if not is_director:
        messages.error(request, 'Chỉ Giám Đốc/Quản lý cấp cao mới có quyền phê duyệt Quỹ lương!')
        return redirect('payroll')
        
    return render(request, 'accounts/payroll_approval.html', {
        'active_page': 'payroll', 
    })


# =============================================================================
# ADMIN VIEWS: User Management (chỉ cho Admin / superuser)
# =============================================================================

@login_required
@user_passes_test(is_admin_user)
def user_list_view(request):
    """
    Danh sách tất cả tài khoản trong hệ thống.
    Chỉ admin (Master/superuser) mới truy cập được.

    Template MỚI: accounts/user_management.html (thay vì user_list.html cũ)
    Context:
      - users: QuerySet tất cả user + profile + role + permissions
      - active_page: để sidebar highlight đúng menu
    """
    users = User.objects.all().select_related('profile__role').prefetch_related(
        'profile__permissions'
    ).order_by('-date_joined')

    # Đảm bảo mọi user đều có profile
    for user in users:
        ensure_profile(user)

    return render(request, 'accounts/user_management.html', {
        'users': users,
        'active_page': 'users',  # Sidebar highlight
    })


@login_required
@user_passes_test(is_admin_user)
def assign_role_view(request, user_id):
    """
    Form thay đổi vai trò của user.
    1. Admin vào /users/5/role/ → thấy dropdown 4 vai trò
    2. Chọn vai trò mới → click "Lưu"
    3. Profile được cập nhật, hiện thông báo thành công

    Template: accounts/assign_role.html
    """
    target_user = get_object_or_404(User, pk=user_id)
    profile = ensure_profile(target_user)

    if request.method == 'POST':
        form = AssignRoleForm(request.POST)
        if form.is_valid():
            profile.role = form.cleaned_data['role']
            profile.save()
            messages.success(
                request,
                f"Vai trò của '{target_user.username}' đã được cập nhật thành "
                f"'{profile.role}' thành công."
                if profile.role else
                f"Đã gỡ vai trò khỏi '{target_user.username}'."
            )
            return redirect('user_list')
    else:
        form = AssignRoleForm(initial={'role': profile.role})

    return render(request, 'accounts/assign_role.html', {
        'form': form,
        'target_user': target_user,
        'active_page': 'users',
    })


@login_required
@user_passes_test(is_admin_user)
def assign_permissions_view(request, user_id):
    """
    Form gán/gỡ quyền cho user.
    1. Admin vào /users/5/permissions/ → thấy checkboxes
    2. Tick = có quyền, bỏ tick = không có
    3. Click "Lưu" → quyền được cập nhật

    Template: accounts/assign_permissions.html
    """
    target_user = get_object_or_404(User, pk=user_id)
    profile = ensure_profile(target_user)

    if request.method == 'POST':
        form = AssignPermissionsForm(request.POST)
        if form.is_valid():
            profile.permissions.set(form.cleaned_data['permissions'])
            messages.success(
                request,
                f"Quyền của '{target_user.username}' đã được cập nhật."
            )
            return redirect('user_list')
    else:
        form = AssignPermissionsForm(
            initial={'permissions': profile.permissions.all()}
        )

    return render(request, 'accounts/assign_permissions.html', {
        'form': form,
        'target_user': target_user,
        'active_page': 'users',
    })


@login_required
@user_passes_test(is_admin_user)
def delete_user_view(request, user_id):
    """
    Xóa tài khoản. Chỉ superuser/Master mới làm được.
    - GET: hiện trang xác nhận
    - POST: xóa user thật
    - Không thể tự xóa mình

    Template: accounts/delete_user.html
    """
    target_user = get_object_or_404(User, pk=user_id)

    if target_user == request.user:
        messages.error(request, "Bạn không thể xóa tài khoản của chính mình.")
        return redirect('user_list')

    if request.method == 'POST':
        username = target_user.username
        target_user.delete()
        messages.success(request, f"Tài khoản '{username}' đã được xóa.")
        return redirect('user_list')

    return render(request, 'accounts/delete_user.html', {
        'target_user': target_user,
        'active_page': 'users',
    })


# =============================================================================
# VIEWS MỚI: Khóa/Mở khóa + Reset Password
# =============================================================================

@login_required
@user_passes_test(is_admin_user)
def toggle_user_active_view(request, user_id):
    """
    Khóa hoặc mở khóa tài khoản user.
    - Chỉ xử lý POST request (an toàn, tránh khóa nhầm qua GET)
    - Đổi trạng thái is_active: True ↔ False
    - Không cho phép khóa chính mình

    Khi is_active=False, Django sẽ KHÔNG cho user đó đăng nhập.
    URL: /users/<id>/toggle-active/
    """
    target_user = get_object_or_404(User, pk=user_id)

    if target_user == request.user:
        messages.error(request, "Bạn không thể khóa tài khoản của chính mình.")
        return redirect('user_list')

    if request.method == 'POST':
        # Đảo trạng thái: active → inactive, inactive → active
        target_user.is_active = not target_user.is_active
        target_user.save()

        if target_user.is_active:
            messages.success(request, f"Đã mở khóa tài khoản '{target_user.username}'.")
        else:
            messages.warning(request, f"Đã khóa tài khoản '{target_user.username}'.")

    return redirect('user_list')


@login_required
@user_passes_test(is_admin_user)
def reset_user_password_view(request, user_id):
    """
    Reset mật khẩu cho user.
    - Chỉ xử lý POST request
    - Đặt mật khẩu mới mặc định: "Password@123"
    - Admin cần thông báo cho user biết mật khẩu mới

    TODO: Sau này có thể nâng cấp thành:
      - Gửi email reset password
      - Tạo mật khẩu ngẫu nhiên
      - Bắt user đổi mật khẩu khi đăng nhập lần đầu sau reset

    URL: /users/<id>/reset-password/
    """
    target_user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        # Đặt mật khẩu mặc định
        default_password = "Password@123"
        target_user.set_password(default_password)
        target_user.save()

        messages.success(
            request,
            f"Mật khẩu của '{target_user.username}' đã được reset thành: {default_password}"
        )

    return redirect('user_list')