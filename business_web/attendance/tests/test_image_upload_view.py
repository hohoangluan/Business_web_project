"""Integration tests for upload_image_base64_view error mapping."""
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from attendance.services.face_api_client import FaceApiError


class UploadImageErrorMappingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', password='secret')
        self.client = Client()
        self.client.login(username='alice', password='secret')
        self.url = reverse('upload_image_base64')

    @patch('attendance.views.image_upload_view.save_employee_face')
    def test_no_face_returns_400_with_code(self, mock_save):
        mock_save.side_effect = FaceApiError('no_face', 'No face detected')
        upload = SimpleUploadedFile(
            'face.jpg', b'\xff\xd8\xfffake', content_type='image/jpeg',
        )
        resp = self.client.post(self.url, {'image': upload})
        self.assertEqual(resp.status_code, 400)
        body = resp.json()
        self.assertFalse(body['success'])
        self.assertEqual(body['code'], 'no_face')

    @patch('attendance.views.image_upload_view.save_employee_face')
    def test_unreachable_returns_502(self, mock_save):
        mock_save.side_effect = FaceApiError('unreachable', 'down')
        upload = SimpleUploadedFile(
            'face.jpg', b'\xff\xd8\xfffake', content_type='image/jpeg',
        )
        resp = self.client.post(self.url, {'image': upload})
        self.assertEqual(resp.status_code, 502)
        body = resp.json()
        self.assertEqual(body['code'], 'unreachable')

    @patch('attendance.views.image_upload_view.save_employee_face')
    def test_timeout_returns_502(self, mock_save):
        mock_save.side_effect = FaceApiError('timeout', 'slow')
        upload = SimpleUploadedFile(
            'face.jpg', b'\xff\xd8\xfffake', content_type='image/jpeg',
        )
        resp = self.client.post(self.url, {'image': upload})
        self.assertEqual(resp.status_code, 502)
