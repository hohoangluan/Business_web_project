import json
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from attendance.models import EmployeeFace, FaceChangeRequest
from django.core.files.uploadedfile import SimpleUploadedFile

DUMMY_GIF = (
    b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00'
    b'!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)


class TestFaceUpload(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='nv001', password='123')
        self.url = reverse('upload_image_base64')
        self.get_url = reverse('get_image_base64')

    @patch('attendance.services.face.face_api_client.register_face_remote')
    def test_att_face_01_self_upload_is_pending(self, mock_register):
        """ATT-FACE-01: NV tự upload → tạo yêu cầu chờ HR duyệt, CHƯA enroll."""
        self.client.force_login(self.user)
        image = SimpleUploadedFile("test_face.gif", DUMMY_GIF, content_type="image/gif")

        response = self.client.post(self.url, {'image': image})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['pending'])

        # Chưa đẩy lên remote, chưa có enrollment có hiệu lực.
        mock_register.assert_not_called()
        self.assertFalse(EmployeeFace.objects.filter(user=self.user).exists())
        req = FaceChangeRequest.objects.get(user=self.user)
        self.assertEqual(req.status, FaceChangeRequest.PENDING)
        self.assertEqual(req.submitted_by, self.user)
        self.assertFalse(req.is_cross_user)

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


class TestFaceChangeWorkflow(TestCase):
    """Chống gian lận: đổi mặt phải HR duyệt mới có hiệu lực."""

    def setUp(self):
        from accounts.models import Role, UserProfile
        self.client = Client()
        self.hr_role = Role.objects.create(name=Role.HR)
        self.emp_role = Role.objects.create(name=Role.EMPLOYEE)
        self.hr = User.objects.create_user(username='hr', password='123')
        UserProfile.objects.create(user=self.hr, role=self.hr_role, employee_id='HR001')
        self.emp = User.objects.create_user(username='emp', password='123')
        UserProfile.objects.create(user=self.emp, role=self.emp_role, employee_id='EMP001')
        self.upload_url = reverse('upload_image_base64')

    def _upload(self, user):
        self.client.force_login(user)
        image = SimpleUploadedFile("f.gif", DUMMY_GIF, content_type="image/gif")
        return self.client.post(self.upload_url, {'image': image})

    @patch('attendance.services.face.face_api_client.register_face_remote')
    def test_hr_upload_applies_immediately(self, mock_register):
        """HR upload (đường tin cậy) → enroll ngay + log đã duyệt."""
        mock_register.return_value = {"status": "success"}
        resp = self._upload(self.hr)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()['pending'])
        mock_register.assert_called_once()
        self.assertTrue(EmployeeFace.objects.filter(user=self.hr).exists())
        req = FaceChangeRequest.objects.get(user=self.hr)
        self.assertEqual(req.status, FaceChangeRequest.APPROVED)

    @patch('attendance.services.face.face_api_client.register_face_remote')
    def test_hr_approve_pending_enrolls(self, mock_register):
        """NV upload pending → HR duyệt → mới gọi remote + tạo EmployeeFace."""
        mock_register.return_value = {"status": "success"}
        self._upload(self.emp)
        mock_register.assert_not_called()
        req = FaceChangeRequest.objects.get(user=self.emp)

        self.client.force_login(self.hr)
        resp = self.client.post(reverse('face_change_approve', args=[req.id]), {'hr_note': 'ok'})
        self.assertEqual(resp.status_code, 302)
        mock_register.assert_called_once()
        self.assertTrue(EmployeeFace.objects.filter(user=self.emp).exists())
        req.refresh_from_db()
        self.assertEqual(req.status, FaceChangeRequest.APPROVED)
        self.assertEqual(req.reviewed_by, self.hr)

    @patch('attendance.services.face.face_api_client.register_face_remote')
    def test_hr_reject_does_not_enroll(self, mock_register):
        """HR từ chối → không gọi remote, không tạo enrollment."""
        self._upload(self.emp)
        req = FaceChangeRequest.objects.get(user=self.emp)
        self.client.force_login(self.hr)
        resp = self.client.post(reverse('face_change_reject', args=[req.id]), {'hr_note': 'no'})
        self.assertEqual(resp.status_code, 302)
        mock_register.assert_not_called()
        self.assertFalse(EmployeeFace.objects.filter(user=self.emp).exists())
        req.refresh_from_db()
        self.assertEqual(req.status, FaceChangeRequest.REJECTED)

    def test_employee_cannot_access_review(self):
        self.client.force_login(self.emp)
        resp = self.client.get(reverse('face_change_review'))
        self.assertEqual(resp.status_code, 302)
