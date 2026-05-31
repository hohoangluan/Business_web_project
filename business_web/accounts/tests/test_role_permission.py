from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile, CustomPermission

class TestRolePermissionView(TestCase):
    def setUp(self):
        self.client = Client()
        # Admin user
        self.admin_user = User.objects.create_user(username='admin001', password='Password123!')
        self.admin_role, _ = Role.objects.get_or_create(name=Role.ADMIN)
        admin_profile, _ = UserProfile.objects.get_or_create(user=self.admin_user, defaults={'employee_id': 'ADMIN'})
        admin_profile.role = self.admin_role
        admin_profile.save()
        
        # Normal user
        self.normal_user = User.objects.create_user(username='nv001', password='Password123!')
        self.normal_profile, _ = UserProfile.objects.get_or_create(user=self.normal_user, defaults={'employee_id': 'NV001'})
        
        # Roles and permissions
        self.manager_role, _ = Role.objects.get_or_create(name=Role.MANAGER)
        self.custom_perm, _ = CustomPermission.objects.get_or_create(
            codename='can_do_something', name='Can do something'
        )
        
        # Test URLs
        self.assign_role_url = reverse('assign_role', args=[self.normal_user.pk])
        self.assign_perms_url = reverse('assign_permissions', args=[self.normal_user.pk])

    def test_acc_role_01_assign_role(self):
        """ACC-ROLE-01: Admin gán role "Manager" cho user"""
        self.client.force_login(self.admin_user)
        
        response = self.client.post(self.assign_role_url, data={
            'role': self.manager_role.pk
        })
        
        self.assertRedirects(response, reverse('user_list'))
        self.normal_profile.refresh_from_db()
        self.assertEqual(self.normal_profile.role, self.manager_role)

    def test_acc_role_03_remove_role(self):
        """ACC-ROLE-03: Admin gỡ role (set None)"""
        # Set a role first
        self.normal_profile.role = self.manager_role
        self.normal_profile.save()
        
        self.client.force_login(self.admin_user)
        response = self.client.post(self.assign_role_url, data={
            'role': ''
        })
        
        self.assertRedirects(response, reverse('user_list'))
        self.normal_profile.refresh_from_db()
        self.assertIsNone(self.normal_profile.role)

    def test_acc_role_04_assign_custom_permission(self):
        """ACC-ROLE-04: Admin gán custom permission cho user"""
        self.client.force_login(self.admin_user)
        
        response = self.client.post(self.assign_perms_url, data={
            'permissions': [self.custom_perm.pk]
        })
        
        self.assertRedirects(response, reverse('user_list'))
        self.normal_profile.refresh_from_db()
        self.assertEqual(self.normal_profile.permissions.count(), 1)
        self.assertIn(self.custom_perm, self.normal_profile.permissions.all())

    def test_acc_role_05_non_admin_access(self):
        """ACC-ROLE-05: Non-Admin truy cập assign role -> bị chặn"""
        self.client.force_login(self.normal_user)
        
        response = self.client.get(self.assign_role_url)
        expected_assign_role_url = f"{reverse('login')}?next={self.assign_role_url}"
        self.assertRedirects(response, expected_assign_role_url)
        
        response = self.client.get(self.assign_perms_url)
        expected_assign_perms_url = f"{reverse('login')}?next={self.assign_perms_url}"
        self.assertRedirects(response, expected_assign_perms_url)
