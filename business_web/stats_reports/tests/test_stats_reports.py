from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile
from employee_profiles.models import EmployeeWorkInfo
from django.utils import timezone

class TestStatsReports(TestCase):
    def setUp(self):
        self.client = Client()
        
        self.hr_role = Role.objects.create(name=Role.HR)
        self.mgr_role = Role.objects.create(name=Role.MANAGER)
        self.emp_role = Role.objects.create(name=Role.EMPLOYEE)
        
        self.hr = User.objects.create_user(username='hr', password='123')
        UserProfile.objects.create(user=self.hr, role=self.hr_role, employee_id='HR001')
        
        self.manager = User.objects.create_user(username='manager', password='123')
        UserProfile.objects.create(user=self.manager, role=self.mgr_role, employee_id='MGR001')
        EmployeeWorkInfo.objects.create(user=self.manager, department='IT')
        
        self.employee = User.objects.create_user(username='employee', password='123')
        UserProfile.objects.create(user=self.employee, role=self.emp_role, employee_id='EMP001')
        EmployeeWorkInfo.objects.create(user=self.employee, manager_user=self.manager, department='IT')
        
        self.url_stats = reverse('statistics')
        self.url_export = reverse('statistics_export_excel')
        self.url_print = reverse('statistics_print')

    def test_statistics_view_employee(self):
        self.client.force_login(self.employee)
        response = self.client.get(self.url_stats)
        self.assertRedirects(response, reverse('dashboard'))

    def test_statistics_view_manager(self):
        self.client.force_login(self.manager)
        response = self.client.get(self.url_stats)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'stats_reports/statistics.html')
        self.assertIn('time_range', response.context)
        self.assertIn('statistics_sections', response.context)

    def test_statistics_export_excel(self):
        self.client.force_login(self.manager)
        response = self.client.get(self.url_export)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertTrue(response['Content-Disposition'].startswith('attachment; filename='))

    def test_statistics_print(self):
        self.client.force_login(self.hr)
        response = self.client.get(self.url_print)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'stats_reports/statistics_print.html')
