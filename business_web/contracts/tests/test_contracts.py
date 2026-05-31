from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile
from contracts.models import ContractInfo
from datetime import timedelta
from django.utils import timezone

class TestContracts(TestCase):
    def setUp(self):
        self.client = Client()
        
        self.hr_role = Role.objects.create(name=Role.HR)
        self.emp_role = Role.objects.create(name=Role.EMPLOYEE)
        
        self.hr = User.objects.create_user(username='hr', password='123')
        UserProfile.objects.create(user=self.hr, role=self.hr_role, employee_id='HR001')
        
        self.employee = User.objects.create_user(username='employee', password='123')
        UserProfile.objects.create(user=self.employee, role=self.emp_role, employee_id='EMP001')
        
        self.today = timezone.localdate()
        self.end_date_soon = self.today + timedelta(days=15)
        
        ContractInfo.objects.create(
            user=self.employee,
            contract_number='HD-001',
            contract_type='Thử việc',
            contract_signed_date='01/01/2026',
            contract_start_date='01/01/2026',
            contract_end_date=self.end_date_soon.strftime('%d/%m/%Y'),
            contract_annual_leave_days=12,
            contract_standard_shift='08:30 - 17:30'
        )

    def test_contract_view(self):
        """GET /contract/ xem hợp đồng cá nhân"""
        self.client.force_login(self.employee)
        response = self.client.get(reverse('contract'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contracts/contract.html')
        self.assertContains(response, 'HD-001')
        self.assertContains(response, 'Thử việc')

    def test_hr_expiring_contracts_view(self):
        """GET /hr/contracts/expiring/ chỉ dành cho HR"""
        self.client.force_login(self.employee)
        response = self.client.get(reverse('hr_expiring_contracts'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login'))) # Access denied
        
        self.client.force_login(self.hr)
        response = self.client.get(reverse('hr_expiring_contracts'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contracts/hr_expiring_contracts.html')
        self.assertContains(response, 'HD-001')

    def test_hr_send_reminder(self):
        """POST /hr/contracts/reminder/ gửi nhắc nhở tái ký"""
        self.client.force_login(self.hr)
        response = self.client.post(reverse('hr_send_reminder', args=[self.employee.id]))
        self.assertRedirects(response, reverse('hr_expiring_contracts'))
