# Data migration to pre-populate the 4 roles and some starter permissions.
# This runs automatically when you run "python3 manage.py migrate".
# It means you don't have to manually create these in the admin panel.

from django.db import migrations


def seed_roles_and_permissions(apps, schema_editor):
    """
    Creates the 4 predefined roles and some useful starter permissions.
    This function is called automatically during migration.
    """
    Role = apps.get_model('accounts', 'Role')
    CustomPermission = apps.get_model('accounts', 'CustomPermission')

    # Create the 4 roles
    roles_data = [
        ('master', 'Full system access. Can manage all users, roles, and permissions.'),
        ('manager', 'Can manage teams and approve requests.'),
        ('leader', 'Can lead a team and assign tasks.'),
        ('employee', 'Standard user with basic access.'),
    ]
    for name, description in roles_data:
        Role.objects.get_or_create(name=name, defaults={'description': description})

    # Create some starter permissions
    permissions_data = [
        ('can_view_reports', 'Can View Reports', 'Allows viewing business reports and analytics.'),
        ('can_export_reports', 'Can Export Reports', 'Allows exporting reports to CSV/PDF.'),
        ('can_manage_team', 'Can Manage Team', 'Allows adding/removing team members.'),
        ('can_approve_leave', 'Can Approve Leave', 'Allows approving or rejecting leave requests.'),
        ('can_manage_projects', 'Can Manage Projects', 'Allows creating and editing projects.'),
        ('can_view_analytics', 'Can View Analytics', 'Allows viewing analytics dashboards.'),
        ('can_manage_settings', 'Can Manage Settings', 'Allows changing system settings.'),
    ]
    for codename, name, description in permissions_data:
        CustomPermission.objects.get_or_create(
            codename=codename,
            defaults={'name': name, 'description': description}
        )


def reverse_seed(apps, schema_editor):
    """Undo the seeding if the migration is reversed."""
    Role = apps.get_model('accounts', 'Role')
    CustomPermission = apps.get_model('accounts', 'CustomPermission')
    Role.objects.all().delete()
    CustomPermission.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_roles_and_permissions, reverse_seed),
    ]
