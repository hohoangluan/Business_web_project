from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile
from accounts.services import DEFAULT_RESET_PASSWORD

class TestAdminManagementView(TestCase):
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
        UserProfile.objects.get_or_create(user=self.normal_user, defaults={'employee_id': 'NV001'})
        
        # Test URLs
        self.user_list_url = reverse('user_list')
        self.delete_user_url = reverse('delete_user', args=[self.normal_user.pk])
        self.toggle_active_url = reverse('toggle_active', args=[self.normal_user.pk])
        self.reset_password_url = reverse('reset_user_password', args=[self.normal_user.pk])

    def test_acc_admin_01_view_user_list_as_admin(self):
        """ACC-ADMIN-01: Admin xem danh sách user"""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.user_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.normal_user, response.context['users'])

    def test_acc_admin_02_view_user_list_as_non_admin(self):
        """ACC-ADMIN-02: Non-Admin/HR truy cập /users/ -> bị chặn"""
        self.client.force_login(self.normal_user)
        response = self.client.get(self.user_list_url)
        expected_url = f"{reverse('login')}?next={self.user_list_url}"
        self.assertRedirects(response, expected_url)

    def test_acc_admin_03_delete_other_user(self):
        """ACC-ADMIN-03: Admin xóa user khác"""
        self.client.force_login(self.admin_user)
        
        # Needs to be POST
        response = self.client.post(self.delete_user_url)
        self.assertRedirects(response, self.user_list_url)
        self.assertFalse(User.objects.filter(pk=self.normal_user.pk).exists())
        self.assertFalse(UserProfile.objects.filter(user=self.normal_user).exists())

    def test_acc_admin_04_delete_self(self):
        """ACC-ADMIN-04: Admin xóa chính mình -> từ chối"""
        self.client.force_login(self.admin_user)
        
        delete_self_url = reverse('delete_user', args=[self.admin_user.pk])
        response = self.client.post(delete_self_url)
        
        self.assertRedirects(response, self.user_list_url)
        self.assertTrue(User.objects.filter(pk=self.admin_user.pk).exists())

    def test_acc_admin_05_06_toggle_user_active(self):
        """ACC-ADMIN-05, 06: Admin khóa và mở khóa tài khoản"""
        self.client.force_login(self.admin_user)
        
        # Test Lock
        response = self.client.post(self.toggle_active_url)
        self.assertRedirects(response, self.user_list_url)
        self.normal_user.refresh_from_db()
        self.assertFalse(self.normal_user.is_active)
        
        # Test Unlock
        response = self.client.post(self.toggle_active_url)
        self.normal_user.refresh_from_db()
        self.assertTrue(self.normal_user.is_active)

    def test_acc_admin_07_toggle_self_active(self):
        """ACC-ADMIN-07: Admin khóa chính mình -> từ chối"""
        self.client.force_login(self.admin_user)
        
        toggle_self_url = reverse('toggle_active', args=[self.admin_user.pk])
        response = self.client.post(toggle_self_url)
        
        self.assertRedirects(response, self.user_list_url)
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.is_active)

    def test_acc_admin_08_reset_user_password(self):
        """ACC-ADMIN-08: Admin reset password user"""
        self.client.force_login(self.admin_user)
        
        response = self.client.post(self.reset_password_url)
        self.assertRedirects(response, self.user_list_url)
        
        self.normal_user.refresh_from_db()
        self.assertTrue(self.normal_user.check_password(DEFAULT_RESET_PASSWORD))
