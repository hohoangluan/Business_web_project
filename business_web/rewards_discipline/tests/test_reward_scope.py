from django.test import TestCase
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile
from employee_profiles.models import EmployeeWorkInfo
from rewards_discipline.forms import RewardPenaltyForm


class RewardScopeTest(TestCase):
    def setUp(self):
        self.leader_role, _ = Role.objects.get_or_create(name=Role.LEADER)
        self.emp_role, _ = Role.objects.get_or_create(name=Role.EMPLOYEE)
        self.hr_role, _ = Role.objects.get_or_create(name=Role.HR)

        self.leader = User.objects.create_user('lead', password='x')
        UserProfile.objects.create(user=self.leader, role=self.leader_role, employee_id='L1')
        self.sub = User.objects.create_user('sub', password='x')
        UserProfile.objects.create(user=self.sub, role=self.emp_role, employee_id='S1')
        self.other = User.objects.create_user('other', password='x')
        UserProfile.objects.create(user=self.other, role=self.emp_role, employee_id='O1')

        EmployeeWorkInfo.objects.create(user=self.sub, leader_user=self.leader)
        EmployeeWorkInfo.objects.create(user=self.other)  # no supervisor link

    def test_leader_sees_only_subordinates(self):
        form = RewardPenaltyForm(user=self.leader)
        ids = {val for val, _ in form.fields['employee'].choices if val}
        self.assertIn(self.sub.id, ids)
        self.assertNotIn(self.other.id, ids)
