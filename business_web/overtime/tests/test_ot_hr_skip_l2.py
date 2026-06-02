"""FUNC-OT-008: người tạo đơn OT có role HR → sau L1 chuyển thẳng approved (bỏ L2)."""
from datetime import time

from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import Role, UserProfile
from employee_profiles.models import EmployeeWorkInfo
from overtime.models import OvertimeRequest
from overtime.services import approve_overtime_request


class TestOtHrSkipL2(TestCase):
    def setUp(self):
        self.hr_role = Role.objects.create(name=Role.HR)
        self.mgr_role = Role.objects.create(name=Role.MANAGER)
        self.manager = User.objects.create_user(username='mgr', password='123')
        UserProfile.objects.create(user=self.manager, role=self.mgr_role, employee_id='M001')
        # Nhân viên HR, manager trực tiếp là self.manager
        self.hr_emp = User.objects.create_user(username='hremp', password='123')
        UserProfile.objects.create(user=self.hr_emp, role=self.hr_role, employee_id='H001')
        EmployeeWorkInfo.objects.create(user=self.hr_emp, manager_user=self.manager)

    def test_hr_owner_skips_l2(self):
        req = OvertimeRequest.objects.create(
            user=self.hr_emp, overtime_date='2026-06-10',
            start_time=time(18, 0), end_time=time(20, 0), hours='2.0',
            reason='x', status=OvertimeRequest.PENDING,
        )
        ok, _ = approve_overtime_request(self.manager, req.id)
        self.assertTrue(ok)
        req.refresh_from_db()
        # HR → approved luôn sau L1, không dừng ở leader_approved.
        self.assertEqual(req.status, OvertimeRequest.APPROVED)
