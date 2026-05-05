"""
Admin config cho accounts: Role, CustomPermission, UserProfile.
"""
from django.contrib import admin
from .models import Role, CustomPermission, UserProfile


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


@admin.register(CustomPermission)
class CustomPermissionAdmin(admin.ModelAdmin):
    list_display = ('codename', 'name', 'description')
    search_fields = ('codename', 'name')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'full_name', 'employee_id', 'phone_number')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'full_name', 'employee_id')
    filter_horizontal = ('permissions',)
