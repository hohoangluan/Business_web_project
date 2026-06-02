from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
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


class TestLeaveAttachment(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='nvleave', password='123')
        self.client.force_login(self.user)
        self.today = timezone.localdate()

    def test_create_leave_with_attachment(self):
        from datetime import timedelta
        pdf = SimpleUploadedFile('don.pdf', b'%PDF-1.4 fake', content_type='application/pdf')
        resp = self.client.post(reverse('leave'), data={
            'leave_type': 'annual',
            'start_date': (self.today + timedelta(days=1)).isoformat(),
            'end_date': (self.today + timedelta(days=2)).isoformat(),
            'reason': 'Việc gia đình',
            'attachment': pdf,
        })
        from leaves.models import LeaveRequest
        req = LeaveRequest.objects.get(user=self.user)
        self.assertTrue(req.attachment.name.startswith('leaves/attachments/'))

    def test_reject_oversize_attachment(self):
        from datetime import timedelta
        big = SimpleUploadedFile('big.pdf', b'x' * (5 * 1024 * 1024 + 1), content_type='application/pdf')
        from leaves.forms import LeaveRequestForm
        form = LeaveRequestForm(data={
            'leave_type': 'annual',
            'start_date': (self.today + timedelta(days=1)).isoformat(),
            'end_date': (self.today + timedelta(days=2)).isoformat(),
            'reason': 'x',
        }, files={'attachment': big})
        self.assertFalse(form.is_valid())
        self.assertIn('attachment', form.errors)


class TestLeaveQuotaWarning(TestCase):
    """FUNC-LEA-004: vượt quỹ phép → KHÔNG chặn, chỉ cảnh báo; đơn vẫn được gửi."""

    def setUp(self):
        from contracts.models import ContractInfo
        self.user = User.objects.create_user(username='nvquota', password='123')
        UserProfile.objects.create(user=self.user, employee_id='Q001')
        self.client.force_login(self.user)
        self.today = timezone.localdate()
        self._ContractInfo = ContractInfo

    def _make_contract(self, annual_days):
        self._ContractInfo.objects.create(
            user=self.user, is_active=True,
            contract_number='HD-Q', contract_type='Chính thức',
            contract_signed_date='01/01/2026', contract_start_date='01/01/2026',
            contract_annual_leave_days=annual_days,
        )

    def _post_leave(self, days):
        start = self.today + timedelta(days=1)
        end = start + timedelta(days=days - 1)
        return self.client.post(reverse('leave'), data={
            'leave_type': LeaveRequest.ANNUAL,
            'start_date': start.isoformat(),
            'end_date': end.isoformat(),
            'reason': 'Test quota',
        }, follow=True)

    def test_over_quota_still_submits_with_warning(self):
        self._make_contract(annual_days=1)        # quỹ 1 ngày
        resp = self._post_leave(days=3)           # nộp 3 ngày → vượt
        # Đơn VẪN được tạo (không chặn).
        obj = LeaveRequest.objects.get(user=self.user)
        self.assertEqual(obj.status, LeaveRequest.PENDING)
        self.assertEqual(obj.days, Decimal('3.0'))
        # Có thông báo cảnh báo (level WARNING).
        msgs = list(resp.context['messages'])
        self.assertTrue(any('không đủ ngày phép' in m.message for m in msgs))
        self.assertTrue(any(m.level_tag == 'warning' for m in msgs))

    def test_within_quota_success_no_warning(self):
        self._make_contract(annual_days=12)       # quỹ 12 ngày
        resp = self._post_leave(days=2)           # nộp 2 ngày → trong quỹ
        obj = LeaveRequest.objects.get(user=self.user)
        self.assertEqual(obj.days, Decimal('2.0'))
        msgs = list(resp.context['messages'])
        self.assertTrue(any('thành công' in m.message for m in msgs))
        self.assertFalse(any(m.level_tag == 'warning' for m in msgs))


class TestSharedUploadValidator(TestCase):
    """Validator dùng chung common.file_validation.validate_upload."""

    def test_accepts_valid_pdf(self):
        from common.file_validation import validate_upload
        f = SimpleUploadedFile('ok.pdf', b'%PDF-1.4', content_type='application/pdf')
        self.assertIs(validate_upload(f), f)

    def test_none_optional_returns_none(self):
        from common.file_validation import validate_upload
        self.assertIsNone(validate_upload(None))

    def test_none_required_raises(self):
        from django.core.exceptions import ValidationError
        from common.file_validation import validate_upload
        with self.assertRaises(ValidationError):
            validate_upload(None, required=True)

    def test_rejects_oversize(self):
        from django.core.exceptions import ValidationError
        from common.file_validation import validate_upload
        big = SimpleUploadedFile('big.pdf', b'x' * (5 * 1024 * 1024 + 1), content_type='application/pdf')
        with self.assertRaises(ValidationError):
            validate_upload(big)

    def test_rejects_bad_mime(self):
        from django.core.exceptions import ValidationError
        from common.file_validation import validate_upload
        bad = SimpleUploadedFile('x.exe', b'MZ', content_type='application/x-msdownload')
        with self.assertRaises(ValidationError):
            validate_upload(bad)
