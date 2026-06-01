from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from attendance.models import AttendanceRecord, AttendanceAdjustmentRequest
from django.utils import timezone
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile

class TestAdjustment(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='nv001', password='123')
        
        # Create a record that needs adjustment
        today = timezone.localdate()
        self.record = AttendanceRecord.objects.create(
            user=self.user,
            record_date=today - timedelta(days=1),
            check_in_time=timezone.now().replace(hour=8, minute=0, second=0).time(),
            status='no_checkout'
        )
        self.url = reverse('attendance_adjustment', args=[self.record.id])
        
    def test_att_adj_01_submit_valid(self):
        """ATT-ADJ-01 & 02: Gửi yêu cầu điều chỉnh hợp lệ"""
        self.client.force_login(self.user)
        response = self.client.post(self.url, data={
            'reason': 'forgot',
            'reason_detail': 'Quên chấm ra',
            'claimed_check_out_time': '17:30'
        })
        self.assertRedirects(response, reverse('attendance'))
        
        # Check DB
        adj = AttendanceAdjustmentRequest.objects.get(record=self.record)
        self.assertEqual(adj.reason, 'forgot')
        self.assertEqual(adj.reason_detail, 'Quên chấm ra')
        self.assertEqual(adj.claimed_check_out_time.strftime('%H:%M'), '17:30')
        self.assertEqual(adj.status, 'pending')
        self.assertEqual(adj.submitted_by, self.user)
        
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, 'pending_adjustment')

    def test_att_adj_03_already_submitted(self):
        """ATT-ADJ-03: Đã submit -> 409"""
        AttendanceAdjustmentRequest.objects.create(
            record=self.record,
            submitted_by=self.user,
            reason='Old reason',
            claimed_check_out_time='17:00'
        )
        
        self.client.force_login(self.user)
        response = self.client.post(self.url, data={
            'reason': 'forgot',
            'reason_detail': 'New reason',
            'claimed_check_out_time': '18:00'
        })
        self.assertEqual(response.status_code, 409)

    def test_att_adj_invalid_status(self):
        """Record status is not no_checkout -> 400"""
        self.record.status = 'late'
        self.record.save()
        
        self.client.force_login(self.user)
        response = self.client.post(self.url, data={
            'reason': 'forgot',
            'reason_detail': 'Quên chấm ra',
            'claimed_check_out_time': '17:30'
        })
        self.assertEqual(response.status_code, 400)

    def test_att_adj_04_upload_evidence(self):
        """ATT-ADJ-04: Upload file evidence"""
        self.client.force_login(self.user)
        dummy_file = SimpleUploadedFile("evidence.jpg", b"file_content", content_type="image/jpeg")
        response = self.client.post(self.url, data={
            'reason': 'forgot',
            'reason_detail': 'Bị lỗi hệ thống',
            'claimed_check_out_time': '18:00',
            'evidence': dummy_file
        })
        self.assertRedirects(response, reverse('attendance'))
        adj = AttendanceAdjustmentRequest.objects.get(record=self.record)
        self.assertTrue(adj.evidence.name.startswith('attendance/adjustments/'))


class TestAdjustmentReview(TestCase):
    def setUp(self):
        from accounts.models import Role, UserProfile
        self.hr = User.objects.create_user('hruser', password='1')
        hr_role, _ = Role.objects.get_or_create(name='hr')
        UserProfile.objects.create(user=self.hr, role=hr_role, employee_id='HR01')
        self.emp = User.objects.create_user('empadj', password='1')
        today = timezone.localdate()
        self.record = AttendanceRecord.objects.create(
            user=self.emp, record_date=today - timedelta(days=1),
            check_in_time=timezone.now().replace(hour=8, minute=0).time(),
            status='pending_adjustment',
        )
        self.adj = AttendanceAdjustmentRequest.objects.create(
            record=self.record, submitted_by=self.emp, reason='forgot',
            claimed_check_out_time='17:30', status='pending',
        )

    def test_hr_approve_sets_checkout_and_status(self):
        from attendance.services.record.adjustment_review_service import approve_adjustment
        ok, _ = approve_adjustment(self.hr, self.adj.id, 'Đồng ý')
        self.assertTrue(ok)
        self.adj.refresh_from_db(); self.record.refresh_from_db()
        self.assertEqual(self.adj.status, 'approved')
        self.assertEqual(self.adj.reviewed_by, self.hr)
        self.assertEqual(self.record.check_out_time.strftime('%H:%M'), '17:30')
        self.assertEqual(self.record.status, 'on_time')

    def test_hr_reject_resets_record(self):
        from attendance.services.record.adjustment_review_service import reject_adjustment
        ok, _ = reject_adjustment(self.hr, self.adj.id, 'Thiếu chứng từ')
        self.assertTrue(ok)
        self.adj.refresh_from_db(); self.record.refresh_from_db()
        self.assertEqual(self.adj.status, 'rejected')
        self.assertEqual(self.record.status, 'no_checkout')

    def test_non_hr_cannot_access_review(self):
        self.client.force_login(self.emp)
        resp = self.client.get(reverse('attendance_adjustment_review'))
        self.assertEqual(resp.status_code, 302)


class TestAdjustmentModelFields(TestCase):
    def test_create_with_check_in_time(self):
        from datetime import time
        u = User.objects.create_user('nvmodel', password='1')
        rec = AttendanceRecord.objects.create(
            user=u, record_date=timezone.localdate(),
            check_in_time=time(8, 0), status='late',
        )
        adj = AttendanceAdjustmentRequest.objects.create(
            record=rec, submitted_by=u, reason='forgot',
            claimed_check_in_time=time(8, 30),
            claimed_check_out_time=None,
        )
        self.assertEqual(adj.claimed_check_in_time, time(8, 30))
        self.assertIsNone(adj.claimed_check_out_time)


class TestAdjustmentForm(TestCase):
    def _file(self):
        return SimpleUploadedFile('e.jpg', b'x', content_type='image/jpeg')

    def test_requires_at_least_one_time(self):
        from attendance.forms.adjustment.attendance_adjustment_form import AttendanceAdjustmentForm
        form = AttendanceAdjustmentForm(
            data={'reason': 'forgot', 'reason_detail': ''},
            files={'evidence': self._file()},
        )
        self.assertFalse(form.is_valid())

    def test_requires_evidence(self):
        from attendance.forms.adjustment.attendance_adjustment_form import AttendanceAdjustmentForm
        form = AttendanceAdjustmentForm(
            data={'reason': 'forgot', 'claimed_check_out_time': '17:30'},
            files={},
        )
        self.assertFalse(form.is_valid())
        self.assertIn('evidence', form.errors)

    def test_valid_with_one_time_and_evidence(self):
        from attendance.forms.adjustment.attendance_adjustment_form import AttendanceAdjustmentForm
        form = AttendanceAdjustmentForm(
            data={'reason': 'forgot', 'claimed_check_out_time': '17:30'},
            files={'evidence': self._file()},
        )
        self.assertTrue(form.is_valid(), form.errors)
