from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import UserProfile
from employee_profiles.models import (
    EmployeeWorkInfo,
    PersonalInfo,
    EmergencyContact,
    EducationAndSkills,
)

class TestProfileView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='nv001', email='old@example.com', password='Password123!')
        self.profile = UserProfile.objects.create(user=self.user, employee_id='NV001', full_name='Old Name')
        self.personal_info = PersonalInfo.objects.create(user=self.user, gender='Male')
        self.emergency_contact = EmergencyContact.objects.create(user=self.user, contact_name='Wife')
        self.education = EducationAndSkills.objects.create(user=self.user, education_level='Bachelor')
        
        self.profile_url = reverse('profile')

    def test_ep_prof_01_view_profile(self):
        """EP-PROF-01: Employee xem trang hồ sơ cá nhân"""
        self.client.force_login(self.user)
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'NV001')
        self.assertContains(response, 'Old Name')

    def test_ep_prof_02_update_basic_info(self):
        """EP-PROF-02: Cập nhật full_name, email, phone"""
        self.client.force_login(self.user)
        response = self.client.post(self.profile_url, data={
            'full_name': 'New Name',
            'email': 'new@example.com',
            'phone_number': '0987654321',
            # Include other required fields to pass form validation if any, but profile_view might handle partial updates
            # or expect all fields. Let's see if this works. If it needs all fields, we'll see an error in coverage.
            'gender': 'Male',
            'contact_name': 'Wife',
            'education_level': 'Bachelor',
        })
        
        # Check DB
        self.profile.refresh_from_db()
        self.user.refresh_from_db()
        self.personal_info.refresh_from_db()
        
        self.assertEqual(self.profile.full_name, 'New Name')
        self.assertEqual(self.user.email, 'new@example.com')
        self.assertEqual(self.personal_info.phone_number, '0987654321')

    def test_ep_prof_06_duplicate_email(self):
        """EP-PROF-06: Cập nhật email trùng user khác -> lỗi"""
        User.objects.create_user(username='nv002', email='used@example.com', password='Password123!')
        
        self.client.force_login(self.user)
        response = self.client.post(self.profile_url, data={
            'full_name': 'New Name',
            'email': 'used@example.com',
            'phone_number': '0987654321',
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('nay da duoc su dung', response.content.decode('utf-8').lower())
        
        # DB not changed
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'old@example.com')
