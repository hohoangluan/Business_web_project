from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import UserProfile, Role

class TestHRAssignRoleView(TestCase):
    def setUp(self):
        self.client = Client()
        self.hr_user = User.objects.create_user(username='hr001', password='Password123!')
        self.hr_role, _ = Role.objects.get_or_create(name=Role.HR)
        hr_profile = UserProfile.objects.create(user=self.hr_user, employee_id='HR001')
        hr_profile.role = self.hr_role
        hr_profile.save()
        
        self.normal_user = User.objects.create_user(username='nv001', password='Password123!')
        self.normal_profile = UserProfile.objects.create(user=self.normal_user, employee_id='NV001')
        
        self.admin_user = User.objects.create_user(username='admin001', password='Password123!')
        self.admin_role, _ = Role.objects.get_or_create(name=Role.ADMIN)
        admin_profile = UserProfile.objects.create(user=self.admin_user, employee_id='ADMIN')
        admin_profile.role = self.admin_role
        admin_profile.save()
        
        self.manager_role, _ = Role.objects.get_or_create(name=Role.MANAGER)
        
        self.assign_url = reverse('hr_assign_role', args=[self.normal_user.pk])

    def test_ep_role_01_hr_assign_role(self):
        """EP-ROLE-01: HR gán role Employee/Leader/Manager/HR"""
        self.client.force_login(self.hr_user)
        
        response = self.client.post(self.assign_url, data={
            'role': self.manager_role.pk
        })
        
        self.assertRedirects(response, reverse('hr_view_profile', args=[self.normal_user.pk]))
        self.normal_profile.refresh_from_db()
        self.assertEqual(self.normal_profile.role, self.manager_role)

    def test_ep_role_02_hr_assign_admin_denied(self):
        """EP-ROLE-02: HR cố gán role Admin -> từ chối"""
        self.client.force_login(self.hr_user)
        
        response = self.client.post(self.assign_url, data={
            'role': self.admin_role.pk
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('hr_assign_role', args=[self.normal_user.pk]))
        self.normal_profile.refresh_from_db()
        self.assertIsNone(self.normal_profile.role)

    def test_ep_role_03_admin_assigns_via_shared_picker(self):
        """EP-ROLE-03: Admin dùng CHUNG trang card-picker, gán được cả Admin.

        Trang phân role hợp nhất cho HR + Admin. Admin lưu xong → về user_list.
        """
        self.client.force_login(self.admin_user)

        response = self.client.post(self.assign_url, data={
            'role': self.admin_role.pk
        })

        self.assertRedirects(response, reverse('user_list'))
        self.normal_profile.refresh_from_db()
        self.assertEqual(self.normal_profile.role, self.admin_role)

    def test_ep_role_05_admin_get_sees_admin_card(self):
        """EP-ROLE-05: Admin GET trang phân role → có lựa chọn vai trò Admin."""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.assign_url)
        self.assertEqual(response.status_code, 200)
        roles = list(response.context['available_roles'])
        self.assertIn(self.admin_role, roles)

    def test_ep_role_06_hr_get_no_admin_card(self):
        """EP-ROLE-06: HR GET trang phân role → KHÔNG có vai trò Admin."""
        self.client.force_login(self.hr_user)
        response = self.client.get(self.assign_url)
        self.assertEqual(response.status_code, 200)
        roles = list(response.context['available_roles'])
        self.assertNotIn(self.admin_role, roles)

    def test_ep_role_07_role_removed_from_profile_form(self):
        """EP-ROLE-07: form sửa hồ sơ KHÔNG còn field role (chỉ đổi qua trang phân role)."""
        from employee_profiles.forms import EmployeeProfileForm
        form = EmployeeProfileForm()
        self.assertNotIn('role', form.fields)

    def test_ep_role_04_remove_role(self):
        """EP-ROLE-04: Bỏ gán role (set empty) -> role = None"""
        self.normal_profile.role = self.manager_role
        self.normal_profile.save()
        
        self.client.force_login(self.hr_user)
        response = self.client.post(self.assign_url, data={
            'role': ''
        })
        
        self.assertRedirects(response, reverse('hr_view_profile', args=[self.normal_user.pk]))
        self.normal_profile.refresh_from_db()
        self.assertIsNone(self.normal_profile.role)
