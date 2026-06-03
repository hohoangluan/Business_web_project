"""F3 — HR xem được phiếu thưởng/phạt của TẤT CẢ nhân viên (staff), trừ tài khoản Admin."""
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, UserProfile
from rewards_discipline.models import RewardPenalty


class TestRewardsViewScope(TestCase):
    def setUp(self):
        self.client = Client()
        self.hr = User.objects.create_user(username='hr', password='123')
        UserProfile.objects.create(
            user=self.hr, role=Role.objects.create(name=Role.HR), employee_id='HR001'
        )
        self.manager = User.objects.create_user(username='mgr', password='123')
        UserProfile.objects.create(
            user=self.manager, role=Role.objects.create(name=Role.MANAGER), employee_id='MGR1'
        )
        self.admin = User.objects.create_user(username='admin', password='123')
        UserProfile.objects.create(
            user=self.admin, role=Role.objects.create(name=Role.ADMIN), employee_id='ADM1'
        )
        RewardPenalty.objects.create(
            employee=self.manager, record_type=RewardPenalty.REWARD,
            amount=500000, reason_title='PHIEU_MANAGER', proposer=self.hr,
            status=RewardPenalty.APPROVED, application_date=timezone.localdate(),
        )
        self.url = reverse('rewards_penalties')

    def test_hr_can_view_any_employee_records(self):
        """HR xem phiếu của manager (là nhân viên) → ĐƯỢC."""
        self.client.force_login(self.hr)
        resp = self.client.get(self.url, {'employee_id': self.manager.id})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'PHIEU_MANAGER')

    def test_hr_cannot_view_admin_records(self):
        """HR truyền employee_id của Admin → bị chặn (Admin không phải nhân viên)."""
        self.client.force_login(self.hr)
        resp = self.client.get(self.url, {'employee_id': self.admin.id})
        self.assertEqual(resp.status_code, 200)
        msgs = [m.message for m in resp.context['messages']]
        self.assertTrue(any('admin' in m.lower() for m in msgs))
