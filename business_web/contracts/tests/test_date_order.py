"""FUNC-CON-004/005: ràng buộc thứ tự ngày hợp đồng."""
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Role, UserProfile
from contracts.services import validate_contract_date_order


class TestContractDateOrderService(TestCase):
    def test_start_before_signed_rejected(self):
        errs = validate_contract_date_order('10/01/2026', '05/01/2026', '')
        self.assertTrue(any('từ ngày ký' in e for e in errs))

    def test_end_before_start_rejected(self):
        errs = validate_contract_date_order('01/01/2026', '05/01/2026', '02/01/2026')
        self.assertTrue(any('sau ngày bắt đầu' in e for e in errs))

    def test_valid_order_ok(self):
        errs = validate_contract_date_order('01/01/2026', '05/01/2026', '05/01/2027')
        self.assertEqual(errs, [])

    def test_open_ended_end_date_ok(self):
        errs = validate_contract_date_order('01/01/2026', '05/01/2026', '')
        self.assertEqual(errs, [])

    def test_end_equal_start_rejected(self):
        errs = validate_contract_date_order('01/01/2026', '01/01/2026', '01/01/2026')
        self.assertTrue(any('hết hạn' in e for e in errs))


class TestContractDateOrderCreateView(TestCase):
    """Tích hợp: HR tạo hồ sơ với ngày HĐ sai thứ tự → bị chặn."""

    def setUp(self):
        self.client = Client()
        self.hr_role = Role.objects.create(name=Role.HR)
        self.hr = User.objects.create_user(username='hr', password='123')
        UserProfile.objects.create(user=self.hr, role=self.hr_role, employee_id='HR001')
        self.mgr = User.objects.create_user(username='mgr', password='123')
        UserProfile.objects.create(user=self.mgr, employee_id='MGR1')
        self.leader = User.objects.create_user(username='ld', password='123')
        UserProfile.objects.create(user=self.leader, employee_id='LD1')
        self.client.force_login(self.hr)

    def _payload(self, **over):
        data = {
            'employee_id': 'NV900', 'department': 'KD', 'position': 'NV',
            'employee_type': 'Toàn thời gian', 'workplace': 'HN',
            'probation_start': '01/01/2026', 'official_start_date': '01/02/2026',
            'work_status': 'working',
            'manager_user': self.mgr.pk, 'leader_user': self.leader.pk,
            'contract_number': 'HD-900', 'contract_type': 'Chính thức',
            'contract_signed_date': '10/01/2026',
            'contract_start_date': '05/01/2026',  # < ngày ký → sai
            'contract_end_date': '',
            'contract_annual_leave_days': '12',
            'contract_standard_shift': '08:30 - 17:30',
        }
        data.update(over)
        return data

    def test_create_blocked_when_start_before_signed(self):
        resp = self.client.post(reverse('hr_create_profile'), data=self._payload())
        self.assertEqual(resp.status_code, 200)
        msgs = [m.message for m in resp.context['messages']]
        self.assertTrue(any('từ ngày ký' in m for m in msgs))
        self.assertFalse(UserProfile.objects.filter(employee_id='NV900').exists())
