"""
==============================================================================
ACCOUNTS SERVICES - Shared Helpers
==============================================================================
Các helper dùng chung cho toàn hệ thống: kiểm tra quyền, lấy thông tin user...
Các app khác import từ đây: from accounts.services.helpers import ...
==============================================================================
"""

from accounts.models import UserProfile, Role


def ensure_profile(user):
    """
    Đảm bảo user có UserProfile.
    Nếu chưa có (VD: user tạo trước khi có profile system), tự động tạo.
    """
    profile, created = UserProfile.objects.get_or_create(user=user)
    return profile


def ensure_work_info(user):
    """
    Đảm bảo user có EmployeeWorkInfo.
    Import tại đây để tránh circular import.
    """
    from employee_profiles.models import EmployeeWorkInfo
    work_info, created = EmployeeWorkInfo.objects.get_or_create(user=user)
    return work_info


def ensure_contract_info(user):
    """
    Đảm bảo user có ContractInfo.
    Import tại đây để tránh circular import.
    """
    from contracts.models import ContractInfo
    contract_info, created = ContractInfo.objects.get_or_create(user=user)
    return contract_info


def get_user_role_name(user):
    """Trả về tên role đã normalize (lowercase) của user."""
    if not user.is_authenticated:
        return ''
    try:
        role = user.profile.role
    except UserProfile.DoesNotExist:
        return ''
    return role.name.lower() if role and role.name else ''


def user_has_role(user, *role_names):
    """Kiểm tra user có một trong các role được liệt kê không."""
    normalized_roles = {role.lower() for role in role_names}
    return get_user_role_name(user) in normalized_roles


def has_admin_business_access(user):
    """
    Kiểm tra user có quyền admin nghiệp vụ không.
    Superuser chưa gán role vẫn có quyền admin đầy đủ.
    """
    role_name = get_user_role_name(user)
    return role_name == Role.ADMIN or (
        user.is_authenticated and user.is_superuser and not role_name
    )


def is_admin_user(user):
    """Kiểm tra user có quyền quản trị không (cho @user_passes_test)."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return get_user_role_name(user) == Role.ADMIN


def is_hr_user(user):
    """Kiểm tra user có phải HR không (cho @user_passes_test)."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user_has_role(user, Role.HR)


def can_manage_requests(user):
    """HR/Manager/Leader/Admin được duyệt đơn, xử lý ticket..."""
    return has_admin_business_access(user) or user_has_role(
        user, Role.HR, Role.MANAGER, Role.LEADER
    )


def can_manage_work_info(user):
    """HR/Admin được cập nhật hồ sơ nhân sự."""
    return has_admin_business_access(user) or user_has_role(user, Role.HR)


def can_access_statistics(user):
    """HR/Admin/Manager/Leader được xem statistics."""
    return has_admin_business_access(user) or user_has_role(
        user, Role.HR, Role.MANAGER, Role.LEADER
    )


def can_access_evaluations(user):
    """Chỉ Manager và Leader có trang thao tác đánh giá riêng."""
    return user_has_role(user, Role.MANAGER, Role.LEADER)


def can_submit_evaluation_demo(user):
    """Chỉ Manager/Leader có form tạo đánh giá ở bản demo."""
    return can_access_evaluations(user)


def get_user_display_name(user):
    """Ưu tiên full name, fallback về username."""
    profile = ensure_profile(user)
    return profile.full_name or user.username


def get_department_label(user):
    """Lấy nhãn phòng ban từ work_info."""
    work_info = ensure_work_info(user)
    return work_info.department or 'Chưa phân phòng ban'


def get_manager_display_name(user):
    """Lấy tên quản lý trực tiếp."""
    work_info = ensure_work_info(user)
    manager_user = work_info.manager_user
    if not manager_user:
        return 'Chưa gán quản lý'
    return get_user_display_name(manager_user)


def get_leader_display_name(user):
    """Lấy tên leader."""
    work_info = ensure_work_info(user)
    leader_user = work_info.leader_user
    if not leader_user:
        return 'Chưa gán leader'
    return get_user_display_name(leader_user)


def mask_email(email):
    """Ẩn bớt email khi hiển thị ở trang quên mật khẩu."""
    if not email or '@' not in email:
        return email or ''
    local_part, domain = email.split('@', 1)
    if len(local_part) <= 2:
        masked_local = local_part[:1] + '*'
    else:
        masked_local = local_part[0] + ('*' * (len(local_part) - 2)) + local_part[-1]
    return f'{masked_local}@{domain}'
