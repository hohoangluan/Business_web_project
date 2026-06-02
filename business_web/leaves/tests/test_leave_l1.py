"""FUNC-LEA-011: chỉ leader/manager trực tiếp của NV mới duyệt L1."""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import Role, UserProfile
from employee_profiles.models import EmployeeWorkInfo
from leaves.models import LeaveRequest
from leaves.services import approve_leave_request


class TestLeaveL1Supervisor(TestCase):
    def setUp(self):
        self.mgr_role = Role.objects.create(name=Role.MANAGER)
        self.emp_role = Role.objects.create(name=Role.EMPLOYEE)
        self.manager = User.objects.create_user(username='mgr', password='123')
        UserProfile.objects.create(user=self.manager, role=self.mgr_role, employee_id='M001')
        self.outsider = User.objects.create_user(username='outsider', password='123')
        UserProfile.objects.create(user=self.outsider, role=self.mgr_role, employee_id='M002')
        self.emp = User.objects.create_user(username='emp', password='123')
        UserProfile.objects.create(user=self.emp, role=self.emp_role, employee_id='E001')
        EmployeeWorkInfo.objects.create(user=self.emp, manager_user=self.manager)

    def _leave(self):
        return LeaveRequest.objects.create(
            user=self.emp, leave_type=LeaveRequest.ANNUAL,
            start_date='2026-07-01', end_date='2026-07-02',
            days=Decimal('2.0'), status=LeaveRequest.PENDING,
        )

    def test_non_supervisor_cannot_approve_l1(self):
        req = self._leave()
        ok, msg = approve_leave_request(self.outsider, req.id)
        self.assertFalse(ok)
        req.refresh_from_db()
        self.assertEqual(req.status, LeaveRequest.PENDING)

    def test_direct_supervisor_approves_l1(self):
        req = self._leave()
        ok, _ = approve_leave_request(self.manager, req.id)
        self.assertTrue(ok)
        req.refresh_from_db()
        self.assertEqual(req.status, LeaveRequest.LEADER_APPROVED)
