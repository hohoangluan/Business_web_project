from django.contrib import admin
from .models import Role, CustomPermission, UserProfile


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """
    Registers the Role model in Django's admin panel.
    This lets you manage roles at /admin/accounts/role/.
    """
    list_display = ('name', 'description')


@admin.register(CustomPermission)
class CustomPermissionAdmin(admin.ModelAdmin):
    """
    Registers CustomPermission in Django's admin panel.
    Lets you create/edit/delete permissions at /admin/accounts/custompermission/.
    """
    list_display = ('codename', 'name', 'description')
    search_fields = ('codename', 'name')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Registers UserProfile in Django's admin panel.
    Lets you see and edit user profiles at /admin/accounts/userprofile/.
    """
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')
    filter_horizontal = ('permissions',)
