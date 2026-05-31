from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile
from employee_profiles.models import EmployeeWorkInfo
from performance.models import Evaluation, EvaluationCategory
from django.utils import timezone

class TestPerformance(TestCase):
    def setUp(self):
        self.client = Client()
        
        self.hr_role = Role.objects.create(name=Role.HR)
        self.mgr_role = Role.objects.create(name=Role.MANAGER)
        self.emp_role = Role.objects.create(name=Role.EMPLOYEE)
        
        self.hr = User.objects.create_user(username='hr', password='123')
        UserProfile.objects.create(user=self.hr, role=self.hr_role, employee_id='HR001')
        
        self.manager = User.objects.create_user(username='manager', password='123')
        UserProfile.objects.create(user=self.manager, role=self.mgr_role, employee_id='MGR001')
        
        self.employee = User.objects.create_user(username='employee', password='123')
        UserProfile.objects.create(user=self.employee, role=self.emp_role, employee_id='EMP001')
        
        EmployeeWorkInfo.objects.create(user=self.manager, department='IT')
        EmployeeWorkInfo.objects.create(user=self.employee, manager_user=self.manager, department='IT')
        
        self.category, _ = EvaluationCategory.objects.get_or_create(name='Chuyên cần', defaults={'description': 'Đánh giá chuyên cần'})
        
        self.today = timezone.localdate()
        self.url_evaluations = reverse('evaluations')

    def test_evaluations_view_get(self):
        """GET /evaluations/ hiển thị danh sách đánh giá"""
        self.client.force_login(self.manager)
        response = self.client.get(self.url_evaluations)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'performance/evaluations.html')

    def test_manager_create_evaluation(self):
        """Manager tạo đánh giá cho nhân viên"""
        self.client.force_login(self.manager)
        # Note: In performance/views/__init__.py, manager might submit with action=submit or draft
        url = f"{self.url_evaluations}?employee={self.employee.username}"
        response = self.client.post(url, data={
            'employee_username': self.employee.username,
            'category': self.category.id,
            'rating': 'A',
            'evaluation_date': self.today.strftime('%Y-%m-%d'),
            'evaluation_content': 'Làm việc tốt',
            'action': 'submit'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_state']['errors'], {})
        
        eval = Evaluation.objects.get(employee=self.employee)
        self.assertEqual(eval.status, 'submitted')
        self.assertEqual(eval.rating, 'A')

    def test_hr_acknowledge_evaluation(self):
        """HR xác nhận đánh giá"""
        eval = Evaluation.objects.create(
            employee=self.employee,
            reviewer=self.manager,
            category=self.category,
            status='submitted',
            rating='A',
            evaluation_date=self.today,
            content='Test content'
        )
        
        self.client.force_login(self.hr)
        url = reverse('evaluation_acknowledge', args=[eval.id])
        response = self.client.post(url, data={
            'hr_note': 'Đã ghi nhận'
        })
        self.assertRedirects(response, reverse('evaluation_hr_approval'))
        
        eval.refresh_from_db()
        self.assertEqual(eval.status, 'acknowledged')
        self.assertEqual(eval.hr_note, 'Đã ghi nhận')
