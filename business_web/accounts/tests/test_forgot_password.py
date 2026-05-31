from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import OtpCode
from unittest.mock import patch

class TestForgotPasswordView(TestCase):
    def setUp(self):
        self.client = Client()
        self.forgot_password_url = reverse('forgot_password')
        self.reset_password_url = reverse('reset_password_after_otp')
        self.user = User.objects.create_user(username='nv001', email='nva@example.com', password='Password123!')

    @patch('accounts.views.auth.forgot_password_view.send_otp_email')
    def test_acc_forgot_01_02_request_otp_valid(self, mock_send_email):
        """ACC-FORGOT-01, 02: Yêu cầu OTP với employee_id hợp lệ"""
        mock_send_email.return_value = True
        
        response = self.client.post(self.forgot_password_url, data={
            'step': 'username',
            'username': 'nv001'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['step'], 'code')
        self.assertIn('success_message', response.context)
        
        # Check OTP record created
        self.assertTrue(OtpCode.objects.filter(user=self.user).exists())
        mock_send_email.assert_called_once()

    @patch('accounts.views.auth.forgot_password_view.send_otp_email')
    def test_acc_forgot_03_verify_otp_valid(self, mock_send_email):
        """ACC-FORGOT-03: Nhập OTP đúng -> cho phép đặt mật khẩu mới"""
        mock_send_email.return_value = True
        
        # Generate OTP
        from accounts.services import create_otp_for_user
        otp_record = create_otp_for_user(self.user)
        
        response = self.client.post(self.forgot_password_url, data={
            'step': 'code',
            'username': 'nv001',
            'verification_code': otp_record.code
        })
        
        # Check redirect to reset password
        self.assertRedirects(response, self.reset_password_url)
        # Check session contains otp_verified_username
        self.assertEqual(self.client.session.get('otp_verified_username'), 'nv001')

    def test_acc_forgot_04_verify_otp_invalid(self):
        """ACC-FORGOT-04: Nhập OTP sai -> từ chối"""
        from accounts.services import create_otp_for_user
        create_otp_for_user(self.user)
        
        response = self.client.post(self.forgot_password_url, data={
            'step': 'code',
            'username': 'nv001',
            'verification_code': '000000' # Assuming 000000 is invalid
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['step'], 'code')
        self.assertIn('error_message', response.context)
        self.assertEqual(response.context['error_message'], 'Mã xác nhận không đúng. Vui lòng kiểm tra lại.')

    def test_acc_forgot_05_reset_password_success(self):
        """ACC-FORGOT-05: Reset password thành công"""
        # Set up session directly to bypass OTP step
        session = self.client.session
        session['otp_verified_username'] = 'nv001'
        session.save()
        
        response = self.client.post(self.reset_password_url, data={
            'new_password1': 'NewStrongPassword123!',
            'new_password2': 'NewStrongPassword123!'
        })
        
        self.assertRedirects(response, reverse('login'))
        
        # Reload user and verify password
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewStrongPassword123!'))
