from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import UserProfile, Role
from employee_profiles.models import EmployeeWorkInfo, PersonalInfo, EmergencyContact, EducationAndSkills
from contracts.models import ContractInfo

class TestEditWorkInfoView(TestCase):
    def setUp(self):
        self.client = Client()
        self.hr_user = User.objects.create_user(username='hr001', password='123')
        self.hr_role = Role.objects.create(name=Role.HR)
        self.hr_profile = UserProfile.objects.create(user=self.hr_user, role=self.hr_role, employee_id='HR001')

        self.manager_role = Role.objects.create(name=Role.MANAGER)
        self.manager_user = User.objects.create_user(username='mgr01', password='123')
        UserProfile.objects.create(user=self.manager_user, role=self.manager_role, employee_id='MGR001')

        self.leader_role = Role.objects.create(name=Role.LEADER)
        self.leader_user = User.objects.create_user(username='ldr01', password='123')
        UserProfile.objects.create(user=self.leader_user, role=self.leader_role, employee_id='LDR001')

        self.normal_user = User.objects.create_user(username='nv001', password='123')
        self.normal_profile = UserProfile.objects.create(user=self.normal_user, employee_id='NV001', full_name='Old Name')
        self.work_info = EmployeeWorkInfo.objects.create(user=self.normal_user)
        self.contract_info = ContractInfo.objects.create(user=self.normal_user)
        self.personal_info = PersonalInfo.objects.create(user=self.normal_user)
        self.emergency_contact = EmergencyContact.objects.create(user=self.normal_user)
        self.education = EducationAndSkills.objects.create(user=self.normal_user)
        
        self.edit_url = reverse('edit_work_info', args=[self.normal_user.pk])

    def test_ep_edit_01_02_edit_all_tables(self):
        """EP-EDIT-01, 02: HR/Admin chỉnh sửa hồ sơ nhân viên (5 bảng)"""
        self.client.force_login(self.hr_user)
        
        response = self.client.post(self.edit_url, data={
            'full_name': 'New Full Name',
            'email': 'new_email@example.com',
            'employee_id': 'NV-1234',
            'department': 'HR',
            'position': 'Manager',
            'employee_type': 'Full-time',
            'workplace': 'Hanoi',
            'probation_start': '2026-01-01',
            'official_start_date': '2026-03-01',
            'work_status': 'working',
            'manager_user': self.manager_user.pk,
            'leader_user': self.leader_user.pk,
            'contract_number': 'HD-999',
            'contract_type': 'Indefinite',
            'contract_signed_date': '2026-01-01',
            'contract_start_date': '2026-01-01',
            'contract_annual_leave_days': '12',
            'contract_standard_shift': 'Morning',
            'gender': 'Female',
            'contact_name': 'Husband',
            'education_level': 'Master'
        })
        
        self.assertRedirects(response, reverse('hr_view_profile', args=[self.normal_user.pk]), msg_prefix=response.content.decode('utf-8'))
        
        self.normal_profile.refresh_from_db()
        self.work_info.refresh_from_db()
        self.contract_info.refresh_from_db()
        self.personal_info.refresh_from_db()
        self.emergency_contact.refresh_from_db()
        self.education.refresh_from_db()
        
        self.assertEqual(self.normal_profile.full_name, 'New Full Name')
        self.assertEqual(self.work_info.department, 'HR')
        self.assertEqual(self.contract_info.contract_number, 'HD-999')
        self.assertEqual(self.personal_info.gender, 'Female')
        self.assertEqual(self.emergency_contact.contact_name, 'Husband')
        self.assertEqual(self.education.education_level, 'Master')

    def test_ep_edit_03_non_hr_access(self):
        """EP-EDIT-03: Non-HR/Admin -> bị chặn"""
        self.client.force_login(self.normal_user)
        
        response = self.client.get(self.edit_url)
        # Should redirect to login or dashboard
        self.assertEqual(response.status_code, 302)
