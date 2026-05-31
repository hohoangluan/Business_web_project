from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from leaves.models import LeaveRequest
from accounts.models import Role, UserProfile
from employee_profiles.models import EmployeeWorkInfo
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

class TestLeaves(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Setup roles
        self.hr_role = Role.objects.create(name=Role.HR)
        self.mgr_role = Role.objects.create(name=Role.MANAGER)
        self.emp_role = Role.objects.create(name=Role.EMPLOYEE)
        
        # Setup users
        self.hr = User.objects.create_user(username='hr', password='123')
        UserProfile.objects.create(user=self.hr, role=self.hr_role, employee_id='HR001')
        
        self.manager = User.objects.create_user(username='manager', password='123')
        UserProfile.objects.create(user=self.manager, role=self.mgr_role, employee_id='MGR001')
        
        self.employee = User.objects.create_user(username='employee', password='123')
        UserProfile.objects.create(user=self.employee, role=self.emp_role, employee_id='EMP001')
        
        # Setup work info so manager is direct supervisor of employee
        EmployeeWorkInfo.objects.create(user=self.employee, manager_user=self.manager)
        
        self.today = timezone.localdate()
        self.url_leave = reverse('leave')

    def test_leave_view_get(self):
        """GET /leave/ hiển thị form và ds đơn"""
        self.client.force_login(self.employee)
        response = self.client.get(self.url_leave)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'leaves/leave.html')
        self.assertIn('form', response.context)
        self.assertIn('requests', response.context)

    def test_leave_create_valid(self):
        """Tạo đơn nghỉ phép hợp lệ"""
        self.client.force_login(self.employee)
        start_date = self.today + timedelta(days=1)
        end_date = self.today + timedelta(days=2)
        response = self.client.post(self.url_leave, data={
            'leave_type': LeaveRequest.ANNUAL,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'reason': 'Về quê'
        })
        self.assertRedirects(response, self.url_leave)
        
        req = LeaveRequest.objects.get(user=self.employee)
        self.assertEqual(req.status, LeaveRequest.PENDING)
        self.assertEqual(req.days, Decimal('2.0'))
        self.assertEqual(req.reason, 'Về quê')

    def test_leave_create_invalid_date(self):
        """Tạo đơn không hợp lệ: end_date < start_date"""
        self.client.force_login(self.employee)
        start_date = self.today + timedelta(days=2)
        end_date = self.today + timedelta(days=1)
        response = self.client.post(self.url_leave, data={
            'leave_type': LeaveRequest.ANNUAL,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'reason': 'Lỗi'
        })
        self.assertEqual(response.status_code, 200) # Form render with error
        self.assertEqual(LeaveRequest.objects.count(), 0)
        self.assertFormError(response, 'form', 'end_date', 'Ngày kết thúc phải từ ngày bắt đầu trở đi.')

    def test_leave_cancel(self):
        """Hủy đơn pending"""
        req = LeaveRequest.objects.create(
            user=self.employee,
            leave_type=LeaveRequest.ANNUAL,
            start_date=self.today,
            end_date=self.today,
            days=Decimal('1.0'),
            status=LeaveRequest.PENDING
        )
        
        self.client.force_login(self.employee)
        url = reverse('leave_cancel', args=[req.id])
        response = self.client.post(url)
        self.assertRedirects(response, self.url_leave)
        self.assertFalse(LeaveRequest.objects.filter(id=req.id).exists())

    def test_leave_cancel_approved(self):
        """Không thể hủy đơn đã duyệt"""
        req = LeaveRequest.objects.create(
            user=self.employee,
            leave_type=LeaveRequest.ANNUAL,
            start_date=self.today,
            end_date=self.today,
            days=Decimal('1.0'),
            status=LeaveRequest.APPROVED
        )
        
        self.client.force_login(self.employee)
        url = reverse('leave_cancel', args=[req.id])
        response = self.client.post(url)
        self.assertTrue(LeaveRequest.objects.filter(id=req.id).exists())

    def test_leave_approval_flow(self):
        """Luồng duyệt 2 bước: Manager -> HR"""
        req = LeaveRequest.objects.create(
            user=self.employee,
            leave_type=LeaveRequest.ANNUAL,
            start_date=self.today,
            end_date=self.today,
            days=Decimal('1.0'),
            status=LeaveRequest.PENDING
        )
        
        # Bước 1: Manager duyệt
        self.client.force_login(self.manager)
        url = reverse('leave_approve', args=[req.id])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('leave_approval'))
        
        req.refresh_from_db()
        self.assertEqual(req.status, LeaveRequest.LEADER_APPROVED)
        self.assertEqual(req.leader_approved_by, self.manager)
        
        # Bước 2: HR duyệt
        self.client.force_login(self.hr)
        response = self.client.post(url)
        
        req.refresh_from_db()
        self.assertEqual(req.status, LeaveRequest.APPROVED)
        self.assertEqual(req.approved_by, self.hr)

    def test_leave_reject(self):
        """Manager từ chối ngay từ bước 1"""
        req = LeaveRequest.objects.create(
            user=self.employee,
            leave_type=LeaveRequest.ANNUAL,
            start_date=self.today,
            end_date=self.today,
            days=Decimal('1.0'),
            status=LeaveRequest.PENDING
        )
        
        self.client.force_login(self.manager)
        url = reverse('leave_reject', args=[req.id])
        response = self.client.post(url, data={'rejected_reason': 'Đang bận dự án'})
        self.assertRedirects(response, reverse('leave_approval'))
        
        req.refresh_from_db()
        self.assertEqual(req.status, LeaveRequest.REJECTED)
        self.assertEqual(req.rejected_reason, 'Đang bận dự án')
