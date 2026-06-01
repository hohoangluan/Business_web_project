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
        from datetime import time
        first_of_month = timezone.localdate().replace(day=1)
        self.record = AttendanceRecord.objects.create(
            user=self.user,
            record_date=first_of_month,
            check_in_time=time(8, 0),
            status='no_checkout'
        )
        self.url = reverse('attendance_adjustment', args=[self.record.id])

    def _evidence(self):
        return SimpleUploadedFile('e.jpg', b'x', content_type='image/jpeg')

    def test_att_adj_01_submit_valid(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data={
            'reason': 'forgot',
            'reason_detail': 'Quên chấm ra',
            'claimed_check_out_time': '17:30',
            'evidence': self._evidence(),
        })
        self.assertRedirects(response, reverse('attendance'))
        adj = AttendanceAdjustmentRequest.objects.get(record=self.record)
        self.assertEqual(adj.status, 'pending')
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, 'pending_adjustment')

    def test_att_adj_03_already_submitted(self):
        """ATT-ADJ-03: Đã submit -> redirect, không tạo bản ghi mới"""
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
            'claimed_check_out_time': '18:00',
            'evidence': self._evidence(),
        })
        self.assertRedirects(response, reverse('attendance'))
        self.assertEqual(
            AttendanceAdjustmentRequest.objects.filter(record=self.record).count(), 1
        )

    def test_att_adj_out_of_month_rejected(self):
        from datetime import time
        last_month = timezone.localdate().replace(day=1) - timedelta(days=1)
        old_rec = AttendanceRecord.objects.create(
            user=self.user, record_date=last_month,
            check_in_time=time(8, 0), status='no_checkout',
        )
        url = reverse('attendance_adjustment', args=[old_rec.id])
        self.client.force_login(self.user)
        self.client.post(url, data={
            'reason': 'forgot', 'claimed_check_out_time': '17:30',
            'evidence': self._evidence(),
        })
        self.assertFalse(AttendanceAdjustmentRequest.objects.filter(record=old_rec).exists())

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


class TestAdjustmentApplyBothTimes(TestCase):
    def setUp(self):
        from accounts.models import Role, UserProfile
        self.hr = User.objects.create_user('hr_apply', password='1')
        hr_role, _ = Role.objects.get_or_create(name='hr')
        UserProfile.objects.create(user=self.hr, role=hr_role, employee_id='HRAP')
        self.emp = User.objects.create_user('emp_apply', password='1')
        from datetime import time
        self.rec_late = AttendanceRecord.objects.create(
            user=self.emp, record_date=timezone.localdate(),
            check_in_time=time(9, 0), check_out_time=time(17, 30), status='late',
        )

    def test_approve_applies_both_times(self):
        from datetime import time
        from attendance.services.record.adjustment_review_service import approve_adjustment
        adj = AttendanceAdjustmentRequest.objects.create(
            record=self.rec_late, submitted_by=self.emp, reason='technical',
            claimed_check_in_time=time(8, 0), claimed_check_out_time=time(17, 30),
            status='pending',
        )
        ok, _ = approve_adjustment(self.hr, adj.id, 'ok')
        self.assertTrue(ok)
        self.rec_late.refresh_from_db()
        self.assertEqual(self.rec_late.check_in_time, time(8, 0))
        self.assertEqual(self.rec_late.check_out_time, time(17, 30))
        self.assertEqual(self.rec_late.status, 'on_time')

    def test_reject_restores_late_status(self):
        from datetime import time
        from attendance.services.record.adjustment_review_service import reject_adjustment
        self.rec_late.status = 'pending_adjustment'
        self.rec_late.save(update_fields=['status'])
        adj = AttendanceAdjustmentRequest.objects.create(
            record=self.rec_late, submitted_by=self.emp, reason='technical',
            claimed_check_in_time=time(8, 0), status='pending',
        )
        ok, _ = reject_adjustment(self.hr, adj.id, 'thiếu')
        self.assertTrue(ok)
        self.rec_late.refresh_from_db()
        self.assertEqual(self.rec_late.status, 'late')

    def test_reject_restores_no_checkout(self):
        from datetime import time
        from attendance.services.record.adjustment_review_service import reject_adjustment
        rec = AttendanceRecord.objects.create(
            user=self.emp, record_date=timezone.localdate() - timedelta(days=2),
            check_in_time=time(8, 0), check_out_time=None, status='pending_adjustment',
        )
        adj = AttendanceAdjustmentRequest.objects.create(
            record=rec, submitted_by=self.emp, reason='forgot',
            claimed_check_out_time=time(17, 30), status='pending',
        )
        ok, _ = reject_adjustment(self.hr, adj.id, 'x')
        self.assertTrue(ok)
        rec.refresh_from_db()
        self.assertEqual(rec.status, 'no_checkout')


class TestAdjustmentSubmitRoles(TestCase):
    def _evidence(self):
        return SimpleUploadedFile('e.jpg', b'x', content_type='image/jpeg')

    def _submit_for_role(self, role_name, username):
        from accounts.models import Role, UserProfile
        from datetime import time
        role, _ = Role.objects.get_or_create(name=role_name)
        u = User.objects.create_user(username, password='1')
        UserProfile.objects.create(user=u, role=role, employee_id=username.upper())
        rec = AttendanceRecord.objects.create(
            user=u, record_date=timezone.localdate(),
            check_in_time=time(9, 0), check_out_time=time(17, 30), status='late',
        )
        self.client.force_login(u)
        resp = self.client.post(
            reverse('attendance_adjustment', args=[rec.id]),
            data={'reason': 'technical', 'claimed_check_in_time': '08:00',
                  'evidence': self._evidence()},
        )
        return rec, resp

    def test_leader_can_submit(self):
        rec, resp = self._submit_for_role('leader', 'ldr_adj')
        self.assertRedirects(resp, reverse('attendance'))
        self.assertTrue(AttendanceAdjustmentRequest.objects.filter(record=rec).exists())

    def test_manager_can_submit(self):
        rec, resp = self._submit_for_role('manager', 'mgr_adj')
        self.assertTrue(AttendanceAdjustmentRequest.objects.filter(record=rec).exists())


class TestAdjustmentReviewNav(TestCase):
    def test_hr_sees_review_link(self):
        from accounts.models import Role, UserProfile
        hr = User.objects.create_user('hr_nav', password='1')
        role, _ = Role.objects.get_or_create(name='hr')
        UserProfile.objects.create(user=hr, role=role, employee_id='HRNAV')
        self.client.force_login(hr)
        resp = self.client.get(reverse('attendance_adjustment_review'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, reverse('attendance_adjustment_review'))
        self.assertContains(resp, 'Duyệt điều chỉnh công')
