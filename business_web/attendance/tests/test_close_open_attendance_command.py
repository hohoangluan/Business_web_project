"""Tests for the close_open_attendance management command."""
from datetime import time, timedelta
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from attendance.models import AttendanceRecord


class CloseOpenAttendanceCommandTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', password='x')
        self.today = timezone.localdate()
        self.yesterday = self.today - timedelta(days=1)
        self.day_before = self.today - timedelta(days=2)

        self.open_yest = AttendanceRecord.objects.create(
            user=self.user, record_date=self.yesterday,
            check_in_time=time(8, 30),
        )
        self.open_today = AttendanceRecord.objects.create(
            user=self.user, record_date=self.today,
            check_in_time=time(8, 30),
        )
        self.closed_old = AttendanceRecord.objects.create(
            user=self.user, record_date=self.day_before,
            check_in_time=time(8, 30), check_out_time=time(17, 30),
            status='on_time',
        )

    def test_default_cutoff_is_today(self):
        out = StringIO()
        call_command('close_open_attendance', stdout=out)
        self.open_yest.refresh_from_db()
        self.open_today.refresh_from_db()
        self.assertEqual(self.open_yest.status, 'no_checkout')
        self.assertEqual(self.open_today.status, '')  # untouched
        self.assertIn('1', out.getvalue())

    def test_idempotent_second_call_zero(self):
        call_command('close_open_attendance')
        out = StringIO()
        call_command('close_open_attendance', stdout=out)
        self.assertIn('0', out.getvalue())

    def test_cutoff_flag(self):
        # cutoff = day_before+1 = yesterday → only day_before records candidates;
        # since closed_old already has check_out_time, nothing changes.
        out = StringIO()
        call_command('close_open_attendance',
                     '--cutoff', self.yesterday.isoformat(), stdout=out)
        self.open_yest.refresh_from_db()
        self.assertEqual(self.open_yest.status, '')  # not yet cutoff
