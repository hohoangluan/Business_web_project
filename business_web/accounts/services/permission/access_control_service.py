"""Access-control helper services."""

from accounts.models import Role
from accounts.services.permission.role_service import get_user_role_name, user_has_role


def has_admin_business_access(user):
    """Return whether the user has admin-level business access."""

    role_name = get_user_role_name(user)
    return role_name == Role.ADMIN or (
        user.is_authenticated and user.is_superuser and not role_name
    )


def can_manage_requests(user):
    """Return whether the user can approve requests.

    Admin chỉ quản lý hệ thống, không xử lý nghiệp vụ nhân sự (duyệt nghỉ/OT,
    khen thưởng, báo cáo). Chỉ HR/Manager/Leader.
    """

    return user_has_role(user, Role.HR, Role.MANAGER, Role.LEADER)


def can_process_tickets(user):
    """Return whether the user can process support tickets.

    Kênh hỗ trợ (yêu cầu/khiếu nại) — chỉ HR + Admin. Quản lý/Leader KHÔNG xử lý
    ticket (chỉ duyệt nghiệp vụ qua can_manage_requests).
    """

    return has_admin_business_access(user) or user_has_role(user, Role.HR)


def can_manage_work_info(user):
    """Return whether the user can access the user-management area.

    Admin (quản trị tài khoản/vai trò) + HR (nghiệp vụ nhân sự). Việc CHỈNH
    thông tin nhân sự chi tiết bị chặn riêng cho Admin trong từng view
    (hr_view_profile / edit_work_info).
    """

    return has_admin_business_access(user) or user_has_role(user, Role.HR)


def can_access_statistics(user):
    """Return whether the user can access statistics pages.

    Admin không được xem thống kê công ty — chỉ HR/Manager/Leader.
    """

    return user_has_role(user, Role.HR, Role.MANAGER, Role.LEADER)


def can_access_evaluations(user):
    """Return whether the user can access evaluation actions."""

    return user_has_role(user, Role.MANAGER, Role.LEADER)


def can_submit_evaluation_demo(user):
    """Return whether the user can submit demo evaluations."""

    return can_access_evaluations(user)


def can_acknowledge_evaluation(user):
    """Return whether the user can acknowledge performance evaluations.

    Admin không được xem/xác nhận đánh giá — chỉ HR.
    """

    return user_has_role(user, Role.HR)

