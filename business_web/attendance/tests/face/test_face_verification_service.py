"""Unit tests for face_verification_service. Mocks face_api_client."""
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from attendance.services.face.face_api_client import FaceApiError
from attendance.services import face_verification_service as svc


class VerifyFaceForUserTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', password='x')

    @patch('attendance.services.face.face_verification_service.face_api_client.recognize_face_remote')
    def test_success_when_employee_id_matches(self, mock_rec):
        mock_rec.return_value = {
            'status': 'success', 'employee_id': str(self.user.id),
            'confidence': '95.4%', 'match_slot': 1,
        }
        out = svc.verify_face_for_user(self.user, b'bytes')
        self.assertTrue(out.success)
        self.assertEqual(out.reason, 'ok')
        self.assertEqual(out.matched_employee_id, str(self.user.id))

    @patch('attendance.services.face.face_verification_service.face_api_client.recognize_face_remote')
    def test_wrong_person_when_employee_id_mismatch(self, mock_rec):
        mock_rec.return_value = {
            'status': 'success', 'employee_id': '9999',
            'confidence': '88.1%', 'match_slot': 1,
        }
        out = svc.verify_face_for_user(self.user, b'bytes')
        self.assertFalse(out.success)
        self.assertEqual(out.reason, 'wrong_person')

    @patch('attendance.services.face.face_verification_service.face_api_client.recognize_face_remote')
    def test_no_match_when_status_fail(self, mock_rec):
        mock_rec.return_value = {'status': 'fail', 'message': 'Unknown'}
        out = svc.verify_face_for_user(self.user, b'bytes')
        self.assertEqual(out.reason, 'no_match')
        self.assertFalse(out.success)

    @patch('attendance.services.face.face_verification_service.face_api_client.recognize_face_remote',
           side_effect=FaceApiError('unreachable', 'down'))
    def test_service_down_on_unreachable(self, _):
        out = svc.verify_face_for_user(self.user, b'bytes')
        self.assertEqual(out.reason, 'service_down')

    @patch('attendance.services.face.face_verification_service.face_api_client.recognize_face_remote',
           side_effect=FaceApiError('no_face', ''))
    def test_no_face_reason(self, _):
        out = svc.verify_face_for_user(self.user, b'bytes')
        self.assertEqual(out.reason, 'no_face')
