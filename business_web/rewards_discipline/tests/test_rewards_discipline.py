from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile
from employee_profiles.models import EmployeeWorkInfo
from rewards_discipline.models import RewardPenalty
from django.utils import timezone

class TestRewardsDiscipline(TestCase):
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
        
        self.url_rewards = reverse('rewards_penalties')
        self.url_approval = reverse('rewards_penalties_approval')
        self.today = timezone.localdate()

    def test_rewards_penalties_view_employee(self):
        self.client.force_login(self.employee)
        response = self.client.get(self.url_rewards)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rewards_discipline/rewards_penalties.html')
        # Employee cannot propose
        self.assertFalse(response.context['can_propose'])

    def test_manager_propose_reward(self):
        self.client.force_login(self.manager)
        response = self.client.post(self.url_rewards, data={
            'action': 'create',
            'employee': self.employee.id,
            'record_type': RewardPenalty.REWARD,
            'amount': 500000,
            'reason_title': 'Hoàn thành dự án sớm',
            'reason_detail': 'Rất tốt',
            'application_date': self.today.strftime('%Y-%m-%d')
        })
        self.assertRedirects(response, self.url_rewards)
        record = RewardPenalty.objects.get(employee=self.employee)
        self.assertEqual(record.status, 'pending')
        self.assertEqual(record.amount, 500000)
        self.assertEqual(record.proposer, self.manager)

    def test_hr_approval_access(self):
        self.client.force_login(self.manager)
        response = self.client.get(self.url_approval)
        # Manager is not HR, should redirect to rewards_penalties
        self.assertRedirects(response, self.url_rewards)
        
        self.client.force_login(self.hr)
        response = self.client.get(self.url_approval)
        self.assertEqual(response.status_code, 200)

    def test_hr_approve_reject_reward(self):
        record = RewardPenalty.objects.create(
            employee=self.employee,
            record_type=RewardPenalty.REWARD,
            amount=200000,
            reason_title='Test approve',
            proposer=self.manager,
            status='pending',
            application_date=self.today
        )
        self.client.force_login(self.hr)
        
        # Approve
        response = self.client.post(self.url_approval, data={
            'action': 'approve',
            'record_id': record.id
        })
        self.assertRedirects(response, self.url_approval)
        record.refresh_from_db()
        self.assertEqual(record.status, 'approved')
        
        # Reject
        record.status = 'pending'
        record.save()
        response = self.client.post(self.url_approval, data={
            'action': 'reject',
            'record_id': record.id
        })
        self.assertRedirects(response, self.url_approval)
        record.refresh_from_db()
        self.assertEqual(record.status, 'rejected')
