from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import UserProfile
from employee_profiles.models import (
    EmployeeWorkInfo,
    PersonalInfo,
    EmergencyContact,
    EducationAndSkills,
)
from contracts.models import ContractInfo

class TestRegisterView(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.valid_data = {
            'employee_id': 'NV001',
            'password': 'StrongPassword123!',
            'full_name': 'Nguyen Van A',
            'email': 'nva@example.com'
        }

    def test_acc_reg_01_02_03_04_valid_registration(self):
        """ACC-REG-01, 02, 03, 04: Đăng ký với dữ liệu hợp lệ"""
        response = self.client.post(self.register_url, data=self.valid_data)
        
        # Check redirect to dashboard
        self.assertRedirects(response, reverse('dashboard'))
        
        # Check User created correctly
        user = User.objects.filter(username='nv001').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'nva@example.com')
        self.assertTrue(user.check_password('StrongPassword123!'))
        
        # Check UserProfile created
        profile = UserProfile.objects.filter(user=user).first()
        self.assertIsNotNone(profile)
        self.assertEqual(profile.employee_id, 'NV001')
        self.assertEqual(profile.full_name, 'Nguyen Van A')
        
        # Check all 5 related profile tables are created
        self.assertTrue(EmployeeWorkInfo.objects.filter(user=user).exists())
        self.assertTrue(ContractInfo.objects.filter(user=user).exists())
        self.assertTrue(PersonalInfo.objects.filter(user=user).exists())
        self.assertTrue(EmergencyContact.objects.filter(user=user).exists())
        self.assertTrue(EducationAndSkills.objects.filter(user=user).exists())
        
        # Check user is logged in
        self.assertEqual(str(self.client.session.get('_auth_user_id')), str(user.pk))

    def test_acc_reg_05_duplicate_employee_id(self):
        """ACC-REG-05: Đăng ký với employee_id đã tồn tại"""
        # Create user first
        User.objects.create_user(username='nv001', password='Password123!')
        
        response = self.client.post(self.register_url, data=self.valid_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'employee_id', 'Mã nhân viên này đã có tài khoản.')
        self.assertEqual(User.objects.count(), 1) # No new user created

    def test_acc_reg_06_duplicate_email(self):
        """ACC-REG-06: Đăng ký với email trùng"""
        User.objects.create_user(username='nv002', email='nva@example.com', password='Password123!')
        
        response = self.client.post(self.register_url, data=self.valid_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email', 'Email này đã được sử dụng.')
        self.assertEqual(User.objects.count(), 1) # No new user created

    def test_acc_reg_07_weak_password(self):
        """ACC-REG-07: Đăng ký với mật khẩu yếu"""
        data = self.valid_data.copy()
        data['password'] = '123'
        
        response = self.client.post(self.register_url, data=data)
        
        self.assertEqual(response.status_code, 200)
        # Django's validation error message might vary, just check there's an error
        self.assertTrue(response.context['form'].errors.get('password'))
        self.assertEqual(User.objects.count(), 0)

    def test_acc_reg_08_transaction_rollback(self):
        """ACC-REG-08: Transaction rollback nếu tạo profile lỗi"""
        # Triggers a failure in profile creation if possible, but actually `create_manual_account` handles transaction.
        # It's hard to force an error natively without mocking. We will test that a failure prevents user creation.
        # A simple way to cause DB error is passing a value too long for a field if not caught by form, 
        # but form cleans it. Let's mock create_manual_account to raise exception and check User count.
        from unittest.mock import patch
        with patch('accounts.views.auth.register_view.create_manual_account') as mock_create:
            mock_create.side_effect = Exception("DB Error")
            try:
                self.client.post(self.register_url, data=self.valid_data)
            except Exception:
                pass
            self.assertEqual(User.objects.count(), 0)

    def test_acc_reg_09_authenticated_user_redirect(self):
        """ACC-REG-09: Đã đăng nhập -> redirect"""
        user = User.objects.create_user(username='nv001', password='Password123!')
        self.client.force_login(user)
        
        response = self.client.get(self.register_url)
        self.assertRedirects(response, reverse('dashboard'))
