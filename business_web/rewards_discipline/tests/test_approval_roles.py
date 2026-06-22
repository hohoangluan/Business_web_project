from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import Role, UserProfile
from rewards_discipline.models import RewardPenalty
from rewards_discipline.services import approve_reward_penalty


class ApprovalRoleTest(TestCase):
    def setUp(self):
        self.leader_role, _ = Role.objects.get_or_create(name=Role.LEADER)
        self.emp_role, _ = Role.objects.get_or_create(name=Role.EMPLOYEE)
        self.leader = User.objects.create_user('lead', password='x')
        UserProfile.objects.create(user=self.leader, role=self.leader_role, employee_id='L1')
        self.emp = User.objects.create_user('emp', password='x')
        UserProfile.objects.create(user=self.emp, role=self.emp_role, employee_id='E1')
        self.rec = RewardPenalty.objects.create(
            employee=self.emp, proposer=self.leader, record_type='reward',
            amount=100, reason_title='t', status=RewardPenalty.PENDING,
            application_date=timezone.localdate(),
        )

    def test_leader_cannot_approve_l1(self):
        ok, _ = approve_reward_penalty(self.leader, self.rec.id)
        self.assertFalse(ok)
