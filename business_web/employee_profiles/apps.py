from django.apps import AppConfig


class EmployeeProfilesConfig(AppConfig):
    """
    App quản lý hồ sơ nhân viên.
    Chứa thông tin công việc, phòng ban, chức vụ, quản lý trực tiếp.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'employee_profiles'
    verbose_name = 'Hồ sơ nhân viên'
