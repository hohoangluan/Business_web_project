"""Tests that AttendanceConfig.ready() calls face_api_client.health_check exactly once and swallows errors."""
from unittest.mock import patch

from django.apps import apps
from django.test import SimpleTestCase


class AttendanceReadyWarmupTests(SimpleTestCase):
    @patch('attendance.services.face_api_client.health_check')
    def test_ready_calls_health_check(self, mock_health_check):
        cfg = apps.get_app_config('attendance')
        cfg.ready()
        mock_health_check.assert_called_once()

    @patch('attendance.services.face_api_client.health_check')
    def test_ready_swallows_exceptions(self, mock_health_check):
        mock_health_check.side_effect = Exception('boom')
        cfg = apps.get_app_config('attendance')
        # Must not raise.
        cfg.ready()
