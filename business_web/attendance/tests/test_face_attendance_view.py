"""Integration tests for face_check_view."""
from datetime import time, timedelta
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone

from attendance.models import AttendanceRecord
from attendance.services.face.face_verification_service import VerifyResult


FIXTURE = Path(__file__).resolve().parent / 'fixtures' / 'sample_face.jpg'


def _upload():
    from django.core.files.uploadedfile import SimpleUploadedFile
    return SimpleUploadedFile('probe.jpg', FIXTURE.read_bytes(),
                              content_type='image/jpeg')


@override_settings(
    FACE_LOCKOUT_MAX_FAILS=3, FACE_LOCKOUT_DURATION_SEC=60,
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                        'LOCATION': 'view-tests'}},
)
class FaceCheckViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user('alice', password='secret')
        self.client = Client()
        self.url = reverse('face_check')

    def test_anonymous_redirect(self):
        resp = self.client.post(self.url, {'image': _upload()})
        self.assertEqual(resp.status_code, 302)

    @patch('attendance.views.face_attendance_view.verify_face_for_user')
    def test_first_scan_creates_check_in(self, mock_verify):
        mock_verify.return_value = VerifyResult(
            success=True, confidence=95.4,
            matched_employee_id=str(self.user.id), reason='ok',
        )
        self.client.login(username='alice', password='secret')
        resp = self.client.post(self.url, {'image': _upload()})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body['action'], 'check_in')
        rec = AttendanceRecord.objects.get(
            user=self.user, record_date=timezone.localdate(),
        )
        self.assertIsNotNone(rec.check_in_time)

    @patch('attendance.views.face_attendance_view.verify_face_for_user')
    def test_second_scan_sets_check_out(self, mock_verify):
        mock_verify.return_value = VerifyResult(
            True, 95.4, str(self.user.id), 'ok',
        )
        AttendanceRecord.objects.create(
            user=self.user, record_date=timezone.localdate(),
            check_in_time=time(8, 30), status='on_time',
        )
        self.client.login(username='alice', password='secret')
        resp = self.client.post(self.url, {'image': _upload()})
        body = resp.json()
        self.assertEqual(body['action'], 'check_out')
        rec = AttendanceRecord.objects.get(
            user=self.user, record_date=timezone.localdate(),
        )
        self.assertIsNotNone(rec.check_out_time)

    @patch('attendance.views.face_attendance_view.verify_face_for_user')
    def test_third_scan_returns_done(self, mock_verify):
        mock_verify.return_value = VerifyResult(
            True, 95.4, str(self.user.id), 'ok',
        )
        AttendanceRecord.objects.create(
            user=self.user, record_date=timezone.localdate(),
            check_in_time=time(8, 30), check_out_time=time(17, 30),
            status='on_time',
        )
        self.client.login(username='alice', password='secret')
        resp = self.client.post(self.url, {'image': _upload()})
        body = resp.json()
        self.assertEqual(body['action'], 'done')

    @patch('attendance.views.face_attendance_view.verify_face_for_user')
    def test_wrong_person_403_and_counter_increments(self, mock_verify):
        mock_verify.return_value = VerifyResult(
            success=False, confidence=88.0, matched_employee_id='9999',
            reason='wrong_person',
        )
        self.client.login(username='alice', password='secret')
        resp = self.client.post(self.url, {'image': _upload()})
        self.assertEqual(resp.status_code, 403)
        body = resp.json()
        self.assertEqual(body['error'], 'wrong_person')
        self.assertIn('fails_left', body)
        self.assertFalse(AttendanceRecord.objects.filter(user=self.user).exists())

    @patch('attendance.views.face_attendance_view.verify_face_for_user')
    def test_three_wrong_attempts_then_locked_423(self, mock_verify):
        mock_verify.return_value = VerifyResult(
            False, 88.0, '9999', 'wrong_person',
        )
        self.client.login(username='alice', password='secret')
        for _ in range(3):
            self.client.post(self.url, {'image': _upload()})
        resp = self.client.post(self.url, {'image': _upload()})
        self.assertEqual(resp.status_code, 423)
        body = resp.json()
        self.assertTrue(body['locked'])
        self.assertGreater(body['retry_after'], 0)

    @patch('attendance.views.face_attendance_view.verify_face_for_user')
    def test_no_match_does_not_increment_counter(self, mock_verify):
        mock_verify.return_value = VerifyResult(
            False, None, None, 'no_match',
        )
        self.client.login(username='alice', password='secret')
        for _ in range(5):
            resp = self.client.post(self.url, {'image': _upload()})
            self.assertEqual(resp.status_code, 401)
            self.assertEqual(resp.json()['error'], 'no_match')
        # Still not locked.
        resp = self.client.post(self.url, {'image': _upload()})
        self.assertEqual(resp.status_code, 401)

    @patch('attendance.views.face_attendance_view.verify_face_for_user')
    def test_service_down_503_no_record(self, mock_verify):
        mock_verify.return_value = VerifyResult(
            False, None, None, 'service_down',
        )
        self.client.login(username='alice', password='secret')
        resp = self.client.post(self.url, {'image': _upload()})
        self.assertEqual(resp.status_code, 503)
        self.assertFalse(AttendanceRecord.objects.filter(user=self.user).exists())

    @patch('attendance.views.face_attendance_view.verify_face_for_user')
    def test_no_face_400(self, mock_verify):
        mock_verify.return_value = VerifyResult(
            False, None, None, 'no_face',
        )
        self.client.login(username='alice', password='secret')
        resp = self.client.post(self.url, {'image': _upload()})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error'], 'no_face_detected')

    @patch('attendance.views.face_attendance_view.verify_face_for_user')
    def test_previous_open_record_echoed(self, mock_verify):
        mock_verify.return_value = VerifyResult(
            True, 95.4, str(self.user.id), 'ok',
        )
        yest = timezone.localdate() - timedelta(days=1)
        AttendanceRecord.objects.create(
            user=self.user, record_date=yest,
            check_in_time=time(8, 30), status='no_checkout',
        )
        self.client.login(username='alice', password='secret')
        resp = self.client.post(self.url, {'image': _upload()})
        body = resp.json()
        self.assertEqual(body['action'], 'check_in')
        self.assertIn('previous_open_record', body)
        self.assertEqual(body['previous_open_record']['date'], yest.isoformat())

    def test_missing_image_returns_400(self):
        self.client.login(username='alice', password='secret')
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, 400)

    @override_settings(
        # Let the request through Django's middleware so our view's own
        # MAX_IMAGE_BYTES check (2 MB) is the one that fires.
        DATA_UPLOAD_MAX_MEMORY_SIZE=10 * 1024 * 1024,
        FILE_UPLOAD_MAX_MEMORY_SIZE=10 * 1024 * 1024,
    )
    def test_too_large_image_400(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        big = SimpleUploadedFile(
            'big.jpg', b'\xff\xd8\xff' + b'a' * (3 * 1024 * 1024),
            content_type='image/jpeg',
        )
        self.client.login(username='alice', password='secret')
        resp = self.client.post(self.url, {'image': big})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error'], 'image_too_large')
