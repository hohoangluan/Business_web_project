import json
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from attendance.models import EmployeeFace
from django.core.files.uploadedfile import SimpleUploadedFile

class TestFaceUpload(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='nv001', password='123')
        self.url = reverse('upload_image_base64')
        self.get_url = reverse('get_image_base64')
        
    @patch('attendance.services.face.face_api_client.register_face_remote')
    def test_att_face_01_upload_valid(self, mock_register):
        """ATT-FACE-01 & 02: Upload ảnh base64 hợp lệ"""
        mock_register.return_value = {
            "status": "success",
            "embedding": [0.1, 0.2, 0.3],
            "message": "Face processed successfully."
        }
        
        self.client.force_login(self.user)
        # Create a tiny valid dummy image (e.g. 1x1 GIF)
        dummy_gif = (
            b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00'
            b'!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        )
        image = SimpleUploadedFile("test_face.gif", dummy_gif, content_type="image/gif")
        
        response = self.client.post(self.url, {'image': image})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Check DB
        face = EmployeeFace.objects.get(user=self.user)
        self.assertEqual(face.content_type, 'image/gif')
        self.assertIsNotNone(face.face_base64)
        self.assertEqual(face.embedding, [0.1, 0.2, 0.3])

    def test_att_face_03_no_data(self):
        """ATT-FACE-03: Upload không có dữ liệu -> lỗi"""
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        
    def test_att_face_04_require_login(self):
        """ATT-FACE-04: User chưa đăng nhập -> redirect login"""
        dummy_gif = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        image = SimpleUploadedFile("test.gif", dummy_gif, content_type="image/gif")
        response = self.client.post(self.url, {'image': image})
        self.assertEqual(response.status_code, 302)

    def test_att_get_01_has_image(self):
        """ATT-GET-01: GET ảnh khi user đã upload"""
        EmployeeFace.objects.create(
            user=self.user,
            face_base64="data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==",
            content_type="image/gif",
            embedding=[0.1, 0.2]
        )
        self.client.force_login(self.user)
        response = self.client.get(self.get_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('base64', data['data'])

    def test_att_get_02_no_image(self):
        """ATT-GET-02: GET ảnh khi user chưa upload"""
        self.client.force_login(self.user)
        response = self.client.get(self.get_url)
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertFalse(data['success'])
