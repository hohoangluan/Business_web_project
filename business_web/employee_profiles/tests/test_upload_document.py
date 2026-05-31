from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from employee_profiles.models import EmployeeDocument
from accounts.models import UserProfile

class TestUploadDocumentView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='nv001', password='Password123!')
        UserProfile.objects.create(user=self.user, employee_id='NV001')
        
        self.upload_url = reverse('upload_document')

    def test_ep_doc_01_upload_valid_document(self):
        """EP-DOC-01: Tải lên tài liệu hợp lệ"""
        self.client.force_login(self.user)
        
        test_file = SimpleUploadedFile("test_doc.pdf", b"file_content", content_type="application/pdf")
        
        response = self.client.post(self.upload_url, data={
            'title': 'Bằng Đại học',
            'document_type': 'degree',
            'file': test_file
        })
        
        self.assertRedirects(response, reverse('profile'))
        self.assertEqual(EmployeeDocument.objects.count(), 1)
        doc = EmployeeDocument.objects.first()
        self.assertEqual(doc.title, 'Bằng Đại học')
        self.assertEqual(doc.document_type, 'degree')
        self.assertEqual(doc.user, self.user)

    def test_ep_doc_03_no_file(self):
        """EP-DOC-03: Không có file tải lên -> báo lỗi"""
        self.client.force_login(self.user)
        
        response = self.client.post(self.upload_url, data={
            'title': 'No file',
            'document_type': 'other'
        })
        
        self.assertRedirects(response, reverse('profile'))
        self.assertEqual(EmployeeDocument.objects.count(), 0)
