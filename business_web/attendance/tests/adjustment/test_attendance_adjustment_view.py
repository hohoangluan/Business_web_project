"""Integration tests for submit_adjustment_view."""
from datetime import time, timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from attendance.models import AttendanceRecord, AttendanceAdjustmentRequest


def _no_checkout_record(user):
    yest = timezone.localdate() - timedelta(days=1)
    return AttendanceRecord.objects.create(
        user=user, record_date=yest,
        check_in_time=time(8, 30), status='no_checkout',
    )


class AdjustmentViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', password='secret')
        self.other = User.objects.create_user('bob', password='secret')
        self.client = Client()
        self.client.login(username='alice', password='secret')

    def test_get_own_no_checkout_record_renders_form(self):
        rec = _no_checkout_record(self.user)
        url = reverse('attendance_adjustment', args=[rec.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'reason')

    def test_get_someone_else_record_404(self):
        rec = _no_checkout_record(self.other)
        url = reverse('attendance_adjustment', args=[rec.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_get_non_no_checkout_record_400(self):
        rec = AttendanceRecord.objects.create(
            user=self.user, record_date=timezone.localdate() - timedelta(days=2),
            check_in_time=time(8, 30), check_out_time=time(17, 30),
            status='on_time',
        )
        url = reverse('attendance_adjustment', args=[rec.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 400)

    def test_post_valid_creates_request_and_flips_status(self):
        rec = _no_checkout_record(self.user)
        url = reverse('attendance_adjustment', args=[rec.id])
        resp = self.client.post(url, {
            'reason': 'forgot',
            'reason_detail': 'Quên bấm chấm ra.',
            'claimed_check_out_time': '17:30',
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        rec.refresh_from_db()
        self.assertEqual(rec.status, 'pending_adjustment')
        self.assertTrue(
            AttendanceAdjustmentRequest.objects.filter(record=rec).exists()
        )

    def test_post_duplicate_returns_409(self):
        rec = _no_checkout_record(self.user)
        AttendanceAdjustmentRequest.objects.create(
            record=rec, submitted_by=self.user,
            reason='forgot', claimed_check_out_time=time(17, 0),
        )
        rec.status = 'pending_adjustment'
        rec.save(update_fields=['status'])
        url = reverse('attendance_adjustment', args=[rec.id])
        resp = self.client.post(url, {
            'reason': 'forgot', 'claimed_check_out_time': '17:30',
        })
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()['error'], 'already_submitted')

    def test_evidence_too_large_rejected(self):
        rec = _no_checkout_record(self.user)
        url = reverse('attendance_adjustment', args=[rec.id])
        big = SimpleUploadedFile(
            'evidence.jpg', b'\xff\xd8\xff' + b'a' * (6 * 1024 * 1024),
            content_type='image/jpeg',
        )
        resp = self.client.post(url, {
            'reason': 'forgot', 'claimed_check_out_time': '17:30',
            'evidence': big,
        })
        self.assertEqual(resp.status_code, 200)  # re-render
        self.assertContains(resp, 'tối đa')  # error message keyword

    def test_evidence_wrong_mime_rejected(self):
        rec = _no_checkout_record(self.user)
        url = reverse('attendance_adjustment', args=[rec.id])
        bogus = SimpleUploadedFile(
            'evidence.exe', b'MZ\x90', content_type='application/octet-stream',
        )
        resp = self.client.post(url, {
            'reason': 'forgot', 'claimed_check_out_time': '17:30',
            'evidence': bogus,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'định dạng')
