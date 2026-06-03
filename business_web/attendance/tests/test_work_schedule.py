"""Gói 2 — cấu hình giờ làm (WorkScheduleConfig) + chấm công dùng config."""
from datetime import time

from django.contrib.auth.models import User
from django.test import TestCase

from attendance.models import WorkScheduleConfig
from attendance.services.record.attendance_logging_service import classify_status
from attendance.services.schedule import (
    get_late_grace_minutes,
    get_work_schedule,
)


class TestWorkScheduleConfig(TestCase):
    def test_get_solo_creates_single_row_with_defaults(self):
        """get_solo() tạo đúng 1 dòng với mặc định 08:30 / 17:30 / 5 phút."""
        config = WorkScheduleConfig.get_solo()
        self.assertEqual(config.shift_start, time(8, 30))
        self.assertEqual(config.shift_end, time(17, 30))
        self.assertEqual(config.late_grace_minutes, 5)
        self.assertEqual(WorkScheduleConfig.objects.count(), 1)

    def test_get_solo_is_idempotent(self):
        """Gọi nhiều lần vẫn 1 dòng (singleton)."""
        first = WorkScheduleConfig.get_solo()
        second = WorkScheduleConfig.get_solo()
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(WorkScheduleConfig.objects.count(), 1)


class TestScheduleResolvers(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='nv001', password='x')

    def test_get_shift_times_uses_config_when_no_contract(self):
        """Không có HĐ → giờ lấy từ WorkScheduleConfig (HR đặt)."""
        from contracts.services import get_shift_times

        config = WorkScheduleConfig.get_solo()
        config.shift_start = time(9, 0)
        config.shift_end = time(18, 0)
        config.save()

        start, end = get_shift_times(self.user)
        self.assertEqual(start, time(9, 0))
        self.assertEqual(end, time(18, 0))

    def test_get_late_grace_minutes_from_config(self):
        config = WorkScheduleConfig.get_solo()
        config.late_grace_minutes = 12
        config.save()
        self.assertEqual(get_late_grace_minutes(), 12)


class TestClassifyStatusGrace(TestCase):
    def test_grace_zero_marks_late(self):
        """grace=0: vào 08:31 khi ca 08:30 → late."""
        status = classify_status(
            time(8, 31), time(17, 30), time(8, 30), time(17, 30), grace_minutes=0
        )
        self.assertEqual(status, 'late')

    def test_grace_window_marks_on_time(self):
        """grace=15: vào 08:40 vẫn on_time."""
        status = classify_status(
            time(8, 40), time(17, 30), time(8, 30), time(17, 30), grace_minutes=15
        )
        self.assertEqual(status, 'on_time')
