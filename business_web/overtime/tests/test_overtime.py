from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from overtime.models import OvertimeRequest
from accounts.models import Role, UserProfile
from employee_profiles.models import EmployeeWorkInfo
from django.utils import timezone
from datetime import timedelta, time
from decimal import Decimal

class TestOvertime(TestCase):
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
        self.url_overtime = reverse('overtime')

    def test_overtime_view_get(self):
        """GET /overtime/ hiển thị form và ds đơn"""
        self.client.force_login(self.employee)
        response = self.client.get(self.url_overtime)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'overtime/overtime.html')
        self.assertIn('form', response.context)
        self.assertIn('requests', response.context)

    def test_overtime_create_valid(self):
        """Tạo đơn tăng ca hợp lệ"""
        self.client.force_login(self.employee)
        response = self.client.post(self.url_overtime, data={
            'overtime_date': self.today.strftime('%Y-%m-%d'),
            'start_time': '18:00',
            'end_time': '20:00',
            'hours': '2',
            'reason': 'Fix bug gấp'
        })
        self.assertRedirects(response, self.url_overtime)
        
        req = OvertimeRequest.objects.get(user=self.employee)
        self.assertEqual(req.status, OvertimeRequest.PENDING)
        self.assertEqual(req.hours, Decimal('2.0'))
        self.assertEqual(req.reason, 'Fix bug gấp')

    def test_overtime_create_invalid_time(self):
        """Tạo đơn không hợp lệ: end_time < start_time"""
        self.client.force_login(self.employee)
        response = self.client.post(self.url_overtime, data={
            'overtime_date': self.today.strftime('%Y-%m-%d'),
            'start_time': '20:00',
            'end_time': '18:00',
            'hours': '2',
            'reason': 'Lỗi'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(OvertimeRequest.objects.count(), 0)
        self.assertFormError(response, 'form', 'end_time', 'Giờ kết thúc phải sau giờ bắt đầu.')

    def test_overtime_cancel(self):
        """Hủy đơn pending"""
        req = OvertimeRequest.objects.create(
            user=self.employee,
            overtime_date=self.today,
            start_time=time(18, 0),
            end_time=time(20, 0),
            hours=Decimal('2.0'),
            status=OvertimeRequest.PENDING
        )
        
        self.client.force_login(self.employee)
        url = reverse('overtime_cancel', args=[req.id])
        response = self.client.post(url)
        self.assertRedirects(response, self.url_overtime)
        self.assertFalse(OvertimeRequest.objects.filter(id=req.id).exists())

    def test_overtime_approval_flow(self):
        """Luồng duyệt 2 bước: Manager -> HR"""
        req = OvertimeRequest.objects.create(
            user=self.employee,
            overtime_date=self.today,
            start_time=time(18, 0),
            end_time=time(20, 0),
            hours=Decimal('2.0'),
            status=OvertimeRequest.PENDING
        )
        
        # Bước 1: Manager duyệt
        self.client.force_login(self.manager)
        url = reverse('overtime_approve', args=[req.id])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('overtime_approval'))
        
        req.refresh_from_db()
        self.assertEqual(req.status, OvertimeRequest.LEADER_APPROVED)
        self.assertEqual(req.leader_approved_by, self.manager)
        
        # Bước 2: HR duyệt
        self.client.force_login(self.hr)
        response = self.client.post(url)
        
        req.refresh_from_db()
        self.assertEqual(req.status, OvertimeRequest.APPROVED)
        self.assertEqual(req.approved_by, self.hr)

    def test_overtime_reject(self):
        """Manager từ chối ngay từ bước 1"""
        req = OvertimeRequest.objects.create(
            user=self.employee,
            overtime_date=self.today,
            start_time=time(18, 0),
            end_time=time(20, 0),
            hours=Decimal('2.0'),
            status=OvertimeRequest.PENDING
        )
        
        self.client.force_login(self.manager)
        url = reverse('overtime_reject', args=[req.id])
        response = self.client.post(url, data={'rejected_reason': 'Không cần thiết'})
        self.assertRedirects(response, reverse('overtime_approval'))
        
        req.refresh_from_db()
        self.assertEqual(req.status, OvertimeRequest.REJECTED)
        self.assertEqual(req.rejected_reason, 'Không cần thiết')


class TestOvertimeAttachment(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='nvot', password='123')
        self.client.force_login(self.user)
        self.today = timezone.localdate()

    def test_create_overtime_with_attachment(self):
        pdf = SimpleUploadedFile('ot.pdf', b'%PDF-1.4 fake', content_type='application/pdf')
        self.client.post(reverse('overtime'), data={
            'overtime_date': self.today.isoformat(),
            'start_time': '18:00',
            'end_time': '20:00',
            'hours': '2.0',
            'reason': 'Chạy deadline',
            'attachment': pdf,
        })
        from overtime.models import OvertimeRequest
        req = OvertimeRequest.objects.get(user=self.user)
        self.assertTrue(req.attachment.name.startswith('overtime/attachments/'))
