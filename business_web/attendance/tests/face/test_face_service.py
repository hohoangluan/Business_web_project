"""Unit tests for the modified save_employee_face. Mocks face_api_client."""
import io
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from attendance.models import EmployeeFace
from attendance.services import face_service
from attendance.services.face.face_api_client import FaceApiError


def make_upload(content=b'\xff\xd8\xfffake jpeg bytes', name='face.jpg',
                content_type='image/jpeg'):
    return SimpleUploadedFile(name, content, content_type=content_type)


class SaveEmployeeFaceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', password='x')

    @patch('attendance.services.face.face_service.face_api_client.register_face_remote')
    def test_first_enrollment_uses_slot_1(self, mock_reg):
        mock_reg.return_value = {'status': 'success', 'embedding': [0.1] * 512}
        face = face_service.save_employee_face(self.user, make_upload())
        self.assertEqual(face.slot_id, 1)
        kwargs = mock_reg.call_args.kwargs
        self.assertEqual(kwargs['slot_id'], 1)
        self.assertEqual(kwargs['employee_id'], str(self.user.id))

    @patch('attendance.services.face.face_service.face_api_client.register_face_remote')
    def test_re_enrollment_reuses_existing_slot(self, mock_reg):
        mock_reg.return_value = {'status': 'success', 'embedding': [0.1] * 512}
        EmployeeFace.objects.create(
            user=self.user, face_base64='old', content_type='image/jpeg',
            slot_id=3,
        )
        face_service.save_employee_face(self.user, make_upload())
        kwargs = mock_reg.call_args.kwargs
        self.assertEqual(kwargs['slot_id'], 3)
        self.assertEqual(
            EmployeeFace.objects.get(user=self.user).slot_id, 3
        )

    @patch('attendance.services.face.face_service.face_api_client.register_face_remote',
           side_effect=FaceApiError('unreachable', 'down'))
    def test_remote_failure_no_local_row_created(self, _):
        with self.assertRaises(FaceApiError):
            face_service.save_employee_face(self.user, make_upload())
        self.assertFalse(EmployeeFace.objects.filter(user=self.user).exists())
