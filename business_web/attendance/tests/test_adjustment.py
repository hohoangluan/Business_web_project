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
