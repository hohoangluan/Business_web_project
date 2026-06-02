"""FUNC-ST-005: số liệu thống kê khớp dữ liệu DB thật (không mock)."""
from datetime import date, time
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import UserProfile
from attendance.models import AttendanceRecord
from leaves.models import LeaveRequest
from overtime.models import OvertimeRequest
from stats_reports.services.statistics_data import build_statistics_records


class TestStatsAccuracy(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='nv', password='123')
        UserProfile.objects.create(user=self.user, employee_id='NV01')
        self.d = date(2026, 6, 1)  # thứ Hai

    def test_aggregates_match_db(self):
        LeaveRequest.objects.create(
            user=self.user, leave_type=LeaveRequest.ANNUAL,
            start_date=self.d, end_date=self.d, days=Decimal('1.0'),
            status=LeaveRequest.APPROVED,
        )
        OvertimeRequest.objects.create(
            user=self.user, overtime_date=self.d,
            start_time=time(18, 0), end_time=time(20, 0), hours=Decimal('2.0'),
            status=OvertimeRequest.APPROVED,
        )
        AttendanceRecord.objects.create(
            user=self.user, record_date=self.d, status='late',
        )

        records = build_statistics_records(
            [self.user], {'start_date': self.d, 'end_date': self.d}
        )
        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual(rec['leave_days'], 1)
        self.assertEqual(rec['leave_requests'], 1)
        self.assertEqual(rec['overtime_hours'], 2.0)
        self.assertEqual(rec['late_count'], 1)
        self.assertEqual(rec['attendance_rate'], 90)
