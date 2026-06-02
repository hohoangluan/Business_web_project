"""FUNC-RW-006: biên số tiền thưởng/phạt — 0 hợp lệ, âm bị chặn.

Điểm chặn là FORM (PositiveIntegerField → form field min_value=0), tức đường
nhập liệu thật của người dùng. (Model.full_clean KHÔNG chặn số âm vì ràng buộc
"positive" nằm ở tầng DB, không phải validator Python.)
"""
from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import Role, UserProfile
from rewards_discipline.forms import RewardPenaltyForm


class TestAmountBoundary(TestCase):
    def setUp(self):
        self.hr_role = Role.objects.create(name=Role.HR)
        self.proposer = User.objects.create_user(username='hr', password='123')
        UserProfile.objects.create(user=self.proposer, role=self.hr_role, employee_id='HR001')
        self.emp = User.objects.create_user(username='emp', password='123')
        UserProfile.objects.create(user=self.emp, employee_id='E001')

    def _form(self, amount):
        return RewardPenaltyForm(data={
            'employee': self.emp.id, 'record_type': 'reward', 'amount': amount,
            'reason_title': 'Lý do', 'reason_detail': 'Chi tiết',
            'application_date': '2026-06-01',
        }, user=self.proposer)

    def test_zero_amount_is_valid(self):
        self.assertTrue(self._form(0).is_valid())

    def test_negative_amount_rejected(self):
        form = self._form(-100)
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
