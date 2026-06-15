"""Định tuyến trạng thái khởi tạo đơn nghỉ phép theo cấu hình quản lý.

- Có ≥1 leader/manager        → PENDING (duyệt L1 bình thường).
- Trống cả 2, nhân viên thường → LEADER_APPROVED (bỏ L1, thẳng HR L2).
- Trống cả 2, nhân viên HR      → APPROVED (tự động duyệt).
"""
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from accounts.models import Role, UserProfile
from employee_profiles.models import EmployeeWorkInfo
from leaves.forms import LeaveRequestForm
from leaves.models import LeaveRequest
from leaves.services import create_leave_request


class TestLeaveInitialStatusRouting(TestCase):
    def setUp(self):
        self.emp_role = Role.objects.create(name=Role.EMPLOYEE)
        self.hr_role = Role.objects.create(name=Role.HR)
        self.mgr_role = Role.objects.create(name=Role.MANAGER)
        self.manager = User.objects.create_user(username='mgr', password='123')
        UserProfile.objects.create(user=self.manager, role=self.mgr_role, employee_id='M001')

    def _make_form(self):
        start = timezone.localdate() + timedelta(days=5)
        end = start + timedelta(days=1)
        form = LeaveRequestForm(data={
            'leave_type': LeaveRequest.ANNUAL,
            'start_date': start.isoformat(),
            'end_date': end.isoformat(),
            'reason': 'test',
        })
        self.assertTrue(form.is_valid(), form.errors)
        return form

    def _emp(self, username, role, leader=None, manager=None):
        user = User.objects.create_user(username=username, password='123')
        UserProfile.objects.create(user=user, role=role, employee_id=username.upper())
        EmployeeWorkInfo.objects.create(user=user, leader_user=leader, manager_user=manager)
        return user

    def test_has_supervisor_stays_pending(self):
        emp = self._emp('emp1', self.emp_role, manager=self.manager)
        obj = create_leave_request(emp, self._make_form())
        self.assertEqual(obj.status, LeaveRequest.PENDING)

    def test_no_supervisor_non_hr_skips_to_hr(self):
        emp = self._emp('emp2', self.emp_role)
        obj = create_leave_request(emp, self._make_form())
        self.assertEqual(obj.status, LeaveRequest.LEADER_APPROVED)

    def test_no_supervisor_hr_auto_approved(self):
        hr = self._emp('hr1', self.hr_role)
        obj = create_leave_request(hr, self._make_form())
        self.assertEqual(obj.status, LeaveRequest.APPROVED)

    def test_no_workinfo_non_hr_skips_to_hr(self):
        user = User.objects.create_user(username='emp3', password='123')
        UserProfile.objects.create(user=user, role=self.emp_role, employee_id='EMP3')
        obj = create_leave_request(user, self._make_form())
        self.assertEqual(obj.status, LeaveRequest.LEADER_APPROVED)
