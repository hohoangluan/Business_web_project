from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import UserProfile, Role
from employee_profiles.models import EmployeeWorkInfo
from contracts.models import ContractInfo

class TestHRCreateProfileView(TestCase):
    def setUp(self):
        self.client = Client()
        self.hr_user = User.objects.create_user(username='hr001', password='Password123!')
        self.hr_role, _ = Role.objects.get_or_create(name=Role.HR)
        hr_profile = UserProfile.objects.create(user=self.hr_user, employee_id='HR001')
        hr_profile.role = self.hr_role
        hr_profile.save()
        
        self.create_url = reverse('hr_create_profile')
        self.valid_data = {
            'employee_id': 'NV002',
            'full_name': 'Nguyen Van B',
            'email': 'nvb@example.com',
            'department': 'IT',
            'position': 'Developer',
            'employee_type': 'Full-time',
            'workplace': 'Hanoi',
            'probation_start': '2026-01-01',
            'official_start_date': '2026-03-01',
            'work_status': 'working',
            'manager_user': self.hr_user.pk, # just use hr_user as manager for testing
            'leader_user': self.hr_user.pk,
            'contract_number': 'HD-2026-001',
            'contract_type': 'Indefinite',
            'contract_signed_date': '2026-01-01',
            'contract_start_date': '2026-01-01',
            'contract_annual_leave_days': '12',
            'contract_standard_shift': 'Morning',
            'auto_create_account': 'on'
        }

    def test_ep_create_01_02_03_04_05_valid_creation(self):
        """EP-CREATE-01, 02, 03, 04, 05: HR tạo hồ sơ với auto_create_account"""
        self.client.force_login(self.hr_user)
        response = self.client.post(self.create_url, data=self.valid_data)
        
        self.assertRedirects(response, reverse('hr_create_profile'))
        
        # Check User created
        user = User.objects.filter(username='nv002').first()
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password('NV002@2026')) # default password logic assumed
        
        # Check Profile
        profile = UserProfile.objects.filter(user=user).first()
        self.assertEqual(profile.employee_id, 'NV002')
        self.assertEqual(profile.full_name, 'Nguyen Van B')
        
        # Check WorkInfo
        work_info = EmployeeWorkInfo.objects.filter(user=user).first()
        self.assertEqual(work_info.department, 'IT')
        self.assertEqual(work_info.position, 'Developer')
        
        # Check ContractInfo
        contract_info = ContractInfo.objects.filter(user=user).first()
        self.assertEqual(contract_info.contract_number, 'HD-2026-001')

    def test_ep_create_06_duplicate_employee_id(self):
        """EP-CREATE-06: Trùng employee_id -> báo lỗi"""
        User.objects.create_user(username='nv002', password='123')
        UserProfile.objects.create(user=User.objects.get(username='nv002'), employee_id='NV002')
        
        self.client.force_login(self.hr_user)
        response = self.client.post(self.create_url, data=self.valid_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('đã tồn tại', response.content.decode('utf-8').lower())

    def test_ep_create_09_non_hr_access(self):
        """EP-CREATE-09: Non-HR truy cập -> bị chặn"""
        normal_user = User.objects.create_user(username='nv003', password='123')
        self.client.force_login(normal_user)
        
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 302)

    def test_ep_create_10_invalid_contract_days(self):
        """EP-CREATE-10: contract_annual_leave_days nhập text -> báo lỗi"""
        self.client.force_login(self.hr_user)
        data = self.valid_data.copy()
        data['contract_annual_leave_days'] = 'abc'
        
        response = self.client.post(self.create_url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Số ngày nghỉ phép/năm phải là số nguyên.', response.content.decode('utf-8'))
