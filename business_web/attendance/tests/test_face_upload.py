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

    @patch('attendance.services.face.face_api_client.register_face_remote')
    def test_att_face_01_self_update_is_pending(self, mock_register):
        """NV đã có mặt, tự upload CẬP NHẬT → pending, lưu ảnh chờ HR, CHƯA enroll lại."""
        EmployeeFace.objects.create(user=self.user, slot_id=1)  # đã enroll trước
        self.client.force_login(self.user)
        image = SimpleUploadedFile("test_face.gif", DUMMY_GIF, content_type="image/gif")
        response = self.client.post(self.url, {'image': image})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['pending'])
        mock_register.assert_not_called()
        req = FaceChangeRequest.objects.get(user=self.user)
        self.assertEqual(req.status, FaceChangeRequest.PENDING)
        self.assertTrue(bool(req.image))          # ảnh được lưu để HR xem
        self.assertEqual(req.submitted_by, self.user)

    @patch('attendance.services.face.face_api_client.register_face_remote')
    def test_att_face_02_first_enrollment_applies(self, mock_register):
        """ATT-FACE-02: NV CHƯA có mặt, tự upload LẦN ĐẦU → tự duyệt + enroll ngay."""
        mock_register.return_value = {"status": "success"}
        self.client.force_login(self.user)
        image = SimpleUploadedFile("first.gif", DUMMY_GIF, content_type="image/gif")

        response = self.client.post(self.url, {'image': image})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['pending'])

        mock_register.assert_called_once()
        self.assertTrue(EmployeeFace.objects.filter(user=self.user).exists())
        req = FaceChangeRequest.objects.get(user=self.user)
        self.assertEqual(req.status, FaceChangeRequest.APPROVED)
        self.assertFalse(bool(req.image))         # auto-approve → không lưu ảnh
        self.assertEqual(req.submitted_by, self.user)

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
        # emp đã có enrollment (HR đăng ký lúc onboarding) → self-upload là CẬP NHẬT
        # nên phải qua bước HR duyệt (đăng ký lần đầu mới được tự duyệt).
        EmployeeFace.objects.create(user=self.emp, slot_id=1)
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
        self.assertFalse(bool(req.image))         # approve → ảnh bị purge

    @patch('attendance.services.face.face_api_client.register_face_remote')
    def test_hr_reject_does_not_enroll(self, mock_register):
        """HR từ chối → không gọi remote, không tạo enrollment."""
        self._upload(self.emp)
        req = FaceChangeRequest.objects.get(user=self.emp)
        self.client.force_login(self.hr)
        resp = self.client.post(reverse('face_change_reject', args=[req.id]), {'hr_note': 'no'})
        self.assertEqual(resp.status_code, 302)
        mock_register.assert_not_called()
        req.refresh_from_db()
        self.assertEqual(req.status, FaceChangeRequest.REJECTED)
        self.assertTrue(bool(req.image))          # reject → GIỮ ảnh làm minh chứng

    def test_employee_cannot_access_review(self):
        self.client.force_login(self.emp)
        resp = self.client.get(reverse('face_change_review'))
        self.assertEqual(resp.status_code, 302)


class TestFaceChangeImageView(TestCase):
    def setUp(self):
        from accounts.models import Role, UserProfile
        self.client = Client()
        self.hr_role = Role.objects.create(name=Role.HR)
        self.emp_role = Role.objects.create(name=Role.EMPLOYEE)
        self.hr = User.objects.create_user(username='hr', password='123')
        UserProfile.objects.create(user=self.hr, role=self.hr_role, employee_id='HR001')
        self.emp = User.objects.create_user(username='emp', password='123')
        UserProfile.objects.create(user=self.emp, role=self.emp_role, employee_id='E001')
        self.stranger = User.objects.create_user(username='str', password='123')
        UserProfile.objects.create(user=self.stranger, role=self.emp_role, employee_id='S001')
        # emp đã có face → upload là cập nhật → pending có ảnh
        EmployeeFace.objects.create(user=self.emp, slot_id=1)
        self.client.force_login(self.emp)
        img = SimpleUploadedFile("f.gif", DUMMY_GIF, content_type="image/gif")
        self.client.post(reverse('upload_image_base64'), {'image': img})
        self.req = FaceChangeRequest.objects.get(user=self.emp)
        self.url = reverse('face_change_image', args=[self.req.id])

    def test_owner_can_view(self):
        self.client.force_login(self.emp)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_hr_can_view(self):
        self.client.force_login(self.hr)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_stranger_404(self):
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_anonymous_redirects(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)

    @patch('attendance.services.face.face_api_client.register_face_remote')
    def test_purged_image_404_after_approve(self, mock_register):
        """Sau approve → ảnh bị purge → xem trả 404 (không còn ảnh)."""
        mock_register.return_value = {"status": "success"}
        from attendance.services.face.face_change_service import approve_face_change
        approve_face_change(self.hr, self.req.id)
        self.client.force_login(self.hr)
        self.assertEqual(self.client.get(self.url).status_code, 404)
