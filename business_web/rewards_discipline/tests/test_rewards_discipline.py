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
        """Employee không có quyền truy cập Khen thưởng & Xử phạt → chuyển hướng Dashboard."""
        self.client.force_login(self.employee)
        response = self.client.get(self.url_rewards)
        self.assertRedirects(response, reverse('dashboard'))

    def test_manager_propose_reward(self):
        """Manager lập phiếu → bỏ L1, vào thẳng chờ HR (leader_approved)."""
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
        self.assertEqual(record.status, RewardPenalty.LEADER_APPROVED)
        self.assertEqual(record.amount, 500000)
        self.assertEqual(record.proposer, self.manager)

    def test_approval_access(self):
        """Manager (L1) và HR (L2) vào được trang duyệt; employee thì không."""
        # Employee bị chặn khỏi trang duyệt (chuyển hướng, không vào được).
        self.client.force_login(self.employee)
        self.assertEqual(self.client.get(self.url_approval).status_code, 302)
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(self.url_approval).status_code, 200)
        self.client.force_login(self.hr)
        self.assertEqual(self.client.get(self.url_approval).status_code, 200)

    def test_hr_approve_reject_reward(self):
        """HR duyệt/từ chối phiếu đang chờ L2 (leader_approved)."""
        record = RewardPenalty.objects.create(
            employee=self.employee, record_type=RewardPenalty.REWARD,
            amount=200000, reason_title='Test approve', proposer=self.manager,
            status=RewardPenalty.LEADER_APPROVED, application_date=self.today,
        )
        self.client.force_login(self.hr)
        response = self.client.post(self.url_approval, data={'action': 'approve', 'record_id': record.id})
        self.assertRedirects(response, self.url_approval)
        record.refresh_from_db()
        self.assertEqual(record.status, RewardPenalty.APPROVED)

        record.status = RewardPenalty.LEADER_APPROVED
        record.save()
        self.client.post(self.url_approval, data={'action': 'reject', 'record_id': record.id})
        record.refresh_from_db()
        self.assertEqual(record.status, RewardPenalty.REJECTED)

    def test_full_two_level_flow_leader_proposes(self):
        """FUNC-RW-005: Leader lập → Manager L1 → HR L2 → approved."""
        leader_role = Role.objects.create(name=Role.LEADER)
        leader = User.objects.create_user(username='leader', password='123')
        UserProfile.objects.create(user=leader, role=leader_role, employee_id='LD001')
        self.client.force_login(leader)
        self.client.post(self.url_rewards, data={
            'action': 'create', 'employee': self.employee.id,
            'record_type': RewardPenalty.PENALTY, 'amount': 0,
            'reason_title': 'Đi trễ', 'reason_detail': 'x',
            'application_date': self.today.strftime('%Y-%m-%d'),
        })
        rec = RewardPenalty.objects.get(employee=self.employee)
        self.assertEqual(rec.status, RewardPenalty.PENDING)

        self.client.force_login(self.manager)
        self.client.post(self.url_approval, data={'action': 'approve', 'record_id': rec.id})
        rec.refresh_from_db()
        self.assertEqual(rec.status, RewardPenalty.LEADER_APPROVED)
        self.assertEqual(rec.leader_approved_by, self.manager)

        self.client.force_login(self.hr)
        self.client.post(self.url_approval, data={'action': 'approve', 'record_id': rec.id})
        rec.refresh_from_db()
        self.assertEqual(rec.status, RewardPenalty.APPROVED)
        self.assertEqual(rec.approved_by, self.hr)

    def test_hr_cannot_do_l1(self):
        """HR không duyệt được phiếu đang ở cấp 1 (phải Manager)."""
        leader_role = Role.objects.create(name=Role.LEADER)
        leader = User.objects.create_user(username='leader2', password='123')
        UserProfile.objects.create(user=leader, role=leader_role, employee_id='LD002')
        rec = RewardPenalty.objects.create(
            employee=self.employee, record_type=RewardPenalty.REWARD, amount=0,
            reason_title='x', proposer=leader, status=RewardPenalty.PENDING,
            application_date=self.today,
        )
        self.client.force_login(self.hr)
        self.client.post(self.url_approval, data={'action': 'approve', 'record_id': rec.id})
        rec.refresh_from_db()
        self.assertEqual(rec.status, RewardPenalty.PENDING)
