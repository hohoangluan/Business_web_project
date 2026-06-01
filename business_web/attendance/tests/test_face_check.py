import json
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from attendance.models import AttendanceRecord
from django.core.files.uploadedfile import SimpleUploadedFile
from attendance.services.face.face_verification_service import VerifyResult

class TestRequestTimeCapture(TestCase):
    def test_check_in_uses_passed_now(self):
        from django.contrib.auth.models import User
        from datetime import datetime
        from django.utils import timezone as tz
        from attendance.services.record.attendance_logging_service import record_check_in
        u = User.objects.create_user('nowuser', password='1')
        fixed = tz.make_aware(datetime(2026, 6, 1, 7, 59, 0))
        rec = record_check_in(u, now=fixed)
        self.assertEqual(rec.check_in_time.strftime('%H:%M'), '07:59')

    def test_slow_verify_does_not_shift_time(self):
        from django.contrib.auth.models import User
        from datetime import datetime
        from django.utils import timezone as tz
        from attendance.services.record.attendance_logging_service import record_check_in
        u = User.objects.create_user('slowuser', password='1')
        early = tz.make_aware(datetime(2026, 6, 1, 8, 0, 0))
        rec = record_check_in(u, now=early)
        self.assertEqual(rec.check_in_time.strftime('%H:%M'), '08:00')


class TestFaceCheck(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='nv001', password='123')
        self.url = reverse('face_check')
        self.dummy_image = SimpleUploadedFile("face.jpg", b"dummy_data", content_type="image/jpeg")

    @patch('attendance.views.face.face_attendance_view.verify_face_for_user')
    def test_att_check_01_03_check_in(self, mock_verify):
        """ATT-CHECK-01 & 03: Chấm công vào thành công"""
        mock_verify.return_value = VerifyResult(True, 99.9, str(self.user.id), 'ok')
        
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'image': self.dummy_image})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['action'], 'check_in')
        
        # ATT-CHECK-02: Kiểm tra record
        today = timezone.localdate()
        record = AttendanceRecord.objects.get(user=self.user, record_date=today)
        self.assertIsNotNone(record.check_in_time)
        self.assertIsNone(record.check_out_time)
        
        # Kiểm tra giờ chấm công có đúng giờ hiện tại không
        now = timezone.localtime().time()
        # Chênh lệch không quá 1 phút (chỉ lấy giờ phút để so)
        self.assertEqual(record.check_in_time.hour, now.hour)
        self.assertAlmostEqual(record.check_in_time.minute, now.minute, delta=1)

    @patch('attendance.views.face.face_attendance_view.verify_face_for_user')
    def test_att_check_04_check_out(self, mock_verify):
        """ATT-CHECK-04: Chấm công lần 2 -> ghi check_out_time"""
        mock_verify.return_value = VerifyResult(True, 99.9, str(self.user.id), 'ok')
        
        today = timezone.localdate()
        AttendanceRecord.objects.create(
            user=self.user,
            record_date=today,
            check_in_time=timezone.now().replace(hour=8, minute=0, second=0).time()
        )
        
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'image': self.dummy_image})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['action'], 'check_out')
        
        record = AttendanceRecord.objects.get(user=self.user, record_date=today)
        self.assertIsNotNone(record.check_out_time)

    @patch('attendance.views.face.face_attendance_view.verify_face_for_user')
    def test_att_check_05_wrong_face(self, mock_verify):
        """ATT-CHECK-05: Khuôn mặt không khớp -> từ chối"""
        mock_verify.return_value = VerifyResult(False, 20.0, 'other_id', 'wrong_person')
        
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'image': self.dummy_image})
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertEqual(data['error'], 'wrong_person')
        
        self.assertFalse(AttendanceRecord.objects.filter(user=self.user).exists())

    @patch('attendance.views.face.face_attendance_view.verify_face_for_user')
    def test_att_check_06_no_face_uploaded(self, mock_verify):
        """ATT-CHECK-06: User chưa đăng ký khuôn mặt"""
        mock_verify.return_value = VerifyResult(False, None, None, 'no_match')
        
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'image': self.dummy_image})
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertEqual(data['error'], 'no_match')
