"""
Admin config cho accounts: Role, CustomPermission, UserProfile.
"""
from django.contrib import admin
from .models import CompanyConfiguration, CustomPermission, Role, UserProfile


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


@admin.register(CustomPermission)
class CustomPermissionAdmin(admin.ModelAdmin):
    list_display = ('codename', 'name', 'description')
    search_fields = ('codename', 'name')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'full_name', 'employee_id', 'get_phone_number')
    list_filter = ('role',)
    search_fields = (
        'user__username',
        'user__email',
        'full_name',
        'user__personal_info__phone_number',
        'employee_id',
    )
    filter_horizontal = ('permissions',)

    def get_phone_number(self, obj):
        return obj.user.personal_info.phone_number if hasattr(obj.user, 'personal_info') else ''
    get_phone_number.short_description = 'Phone Number'


@admin.register(CompanyConfiguration)
class CompanyConfigurationAdmin(admin.ModelAdmin):
    list_display = ('id', 'updated_at')
