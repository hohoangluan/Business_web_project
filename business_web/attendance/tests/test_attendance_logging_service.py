"""DB-backed unit tests for attendance_logging_service."""
from datetime import date, time, timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone

from attendance.models import AttendanceRecord
from attendance.services import attendance_logging_service as svc


@override_settings(WORK_LATE_GRACE_MIN=5)
class DecideNextActionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', password='x')
        self.today = timezone.localdate()

    def test_no_record_returns_check_in(self):
        r = AttendanceRecord(user=self.user, record_date=self.today)
        self.assertEqual(svc.decide_next_action(r), 'check_in')

    def test_only_check_in_returns_check_out(self):
        r = AttendanceRecord.objects.create(
            user=self.user, record_date=self.today,
            check_in_time=time(8, 30),
        )
        self.assertEqual(svc.decide_next_action(r), 'check_out')

    def test_both_set_returns_done(self):
        r = AttendanceRecord.objects.create(
            user=self.user, record_date=self.today,
            check_in_time=time(8, 30), check_out_time=time(17, 30),
        )
        self.assertEqual(svc.decide_next_action(r), 'done')


@override_settings(WORK_LATE_GRACE_MIN=5)
class RecordCheckInTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', password='x')

    @patch('attendance.services.attendance_logging_service.timezone')
    def test_on_time_status_within_grace(self, mock_tz):
        # 8:32 → within 5-min grace after 8:30
        mock_tz.localdate.return_value = date(2026, 5, 27)
        mock_tz.localtime.return_value.time.return_value = time(8, 32)
        r = svc.record_check_in(self.user)
        self.assertEqual(r.status, 'on_time')
        self.assertEqual(r.check_in_time, time(8, 32))

    @patch('attendance.services.attendance_logging_service.timezone')
    def test_late_status_past_grace(self, mock_tz):
        mock_tz.localdate.return_value = date(2026, 5, 27)
        mock_tz.localtime.return_value.time.return_value = time(8, 45)
        r = svc.record_check_in(self.user)
        self.assertEqual(r.status, 'late')

    def test_unique_per_user_date(self):
        today = timezone.localdate()
        svc.record_check_in(self.user)
        # second call must not error; returns same row
        r2 = svc.record_check_in(self.user)
        self.assertEqual(
            AttendanceRecord.objects.filter(user=self.user, record_date=today).count(), 1
        )


class RecordCheckOutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', password='x')
        self.today = timezone.localdate()
        self.record = AttendanceRecord.objects.create(
            user=self.user, record_date=self.today,
            check_in_time=time(8, 30), status='on_time',
        )

    def test_writes_check_out_when_empty(self):
        r = svc.record_check_out(self.user)
        self.assertIsNotNone(r.check_out_time)

    def test_idempotent_does_not_overwrite(self):
        r1 = svc.record_check_out(self.user)
        first_t = r1.check_out_time
        r2 = svc.record_check_out(self.user)
        self.assertEqual(r2.check_out_time, first_t)


class GetOpenPreviousRecordTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', password='x')

    def test_returns_none_when_no_records(self):
        self.assertIsNone(svc.get_open_previous_record(self.user))

    def test_returns_yesterday_open_record(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        rec = AttendanceRecord.objects.create(
            user=self.user, record_date=yesterday,
            check_in_time=time(8, 30),
        )
        self.assertEqual(svc.get_open_previous_record(self.user), rec)

    def test_returns_none_when_yesterday_closed(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        AttendanceRecord.objects.create(
            user=self.user, record_date=yesterday,
            check_in_time=time(8, 30), check_out_time=time(17, 30),
        )
        self.assertIsNone(svc.get_open_previous_record(self.user))

    def test_today_open_record_is_not_previous(self):
        AttendanceRecord.objects.create(
            user=self.user, record_date=timezone.localdate(),
            check_in_time=time(8, 30),
        )
        self.assertIsNone(svc.get_open_previous_record(self.user))


class CloseOpenRecordsBeforeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', password='x')
        self.today = timezone.localdate()
        self.yesterday = self.today - timedelta(days=1)
        self.day_before = self.today - timedelta(days=2)

        self.open_yest = AttendanceRecord.objects.create(
            user=self.user, record_date=self.yesterday,
            check_in_time=time(8, 30),
        )
        self.closed_old = AttendanceRecord.objects.create(
            user=self.user, record_date=self.day_before,
            check_in_time=time(8, 30), check_out_time=time(17, 30),
            status='on_time',
        )
        self.open_today = AttendanceRecord.objects.create(
            user=self.user, record_date=self.today,
            check_in_time=time(8, 30),
        )

    def test_closes_only_past_open_record(self):
        affected = svc.close_open_records_before(self.today)
        self.assertEqual(affected, 1)
        self.open_yest.refresh_from_db()
        self.open_today.refresh_from_db()
        self.closed_old.refresh_from_db()
        self.assertEqual(self.open_yest.status, 'no_checkout')
        self.assertEqual(self.open_today.status, '')  # untouched
        self.assertEqual(self.closed_old.status, 'on_time')

    def test_idempotent_second_call_zero(self):
        svc.close_open_records_before(self.today)
        affected = svc.close_open_records_before(self.today)
        self.assertEqual(affected, 0)
