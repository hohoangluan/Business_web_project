"""Tests for attendance_view context: history + banner."""
from datetime import time, timedelta

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from attendance.models import AttendanceRecord


class AttendanceViewContextTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', password='secret')
        self.client = Client()
        self.client.login(username='alice', password='secret')

    def test_banner_context_absent_when_no_open_previous(self):
        resp = self.client.get(reverse('attendance'))
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.context['open_previous_record'])

    def test_banner_context_present_when_no_checkout_yesterday(self):
        yest = timezone.localdate() - timedelta(days=1)
        rec = AttendanceRecord.objects.create(
            user=self.user, record_date=yest,
            check_in_time=time(8, 30), status='no_checkout',
        )
        resp = self.client.get(reverse('attendance'))
        self.assertEqual(resp.context['open_previous_record'], rec)
        self.assertTrue(resp.context['banner_eligible_for_adjustment'])

    def test_pending_adjustment_banner_read_only(self):
        yest = timezone.localdate() - timedelta(days=1)
        AttendanceRecord.objects.create(
            user=self.user, record_date=yest,
            check_in_time=time(8, 30), status='pending_adjustment',
        )
        resp = self.client.get(reverse('attendance'))
        # pending_adjustment is technically still no_checkout-in-spirit but the
        # banner should switch to read-only.
        self.assertFalse(resp.context['banner_eligible_for_adjustment'])

    def test_history_rows_passed_for_current_month(self):
        today = timezone.localdate()
        AttendanceRecord.objects.create(
            user=self.user, record_date=today,
            check_in_time=time(8, 30), status='on_time',
        )
        resp = self.client.get(reverse('attendance'))
        self.assertEqual(len(resp.context['history_rows']), 1)
