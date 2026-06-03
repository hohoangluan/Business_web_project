"""FUNC-EP-003 / EP-004: validation bắt buộc khi HR tạo hồ sơ."""
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Role, UserProfile


class TestHrCreateValidation(TestCase):
    def setUp(self):
        self.client = Client()
        self.hr_role = Role.objects.create(name=Role.HR)
        self.hr = User.objects.create_user(username='hr', password='123')
        UserProfile.objects.create(user=self.hr, role=self.hr_role, employee_id='HR001')
        self.client.force_login(self.hr)
        self.url = reverse('hr_create_profile')

    def _messages(self, resp):
        return [m.message for m in resp.context['messages']]

    def test_func_ep_003_employee_id_required(self):
        resp = self.client.post(self.url, data={'employee_id': '', 'department': 'Kinh doanh'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Mã nhân viên không được để trống.', self._messages(resp))
        self.assertEqual(User.objects.count(), 1)  # chỉ còn HR

    def test_func_ep_004_department_required(self):
        resp = self.client.post(self.url, data={'employee_id': 'NV999', 'department': ''})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Phòng ban không được để trống.', self._messages(resp))
        self.assertFalse(UserProfile.objects.filter(employee_id='NV999').exists())

    def _full_valid_payload(self, **overrides):
        mgr = User.objects.create_user(username='mgr', password='123')
        UserProfile.objects.create(
            user=mgr, role=Role.objects.get_or_create(name=Role.MANAGER)[0], employee_id='MGR9'
        )
        ldr = User.objects.create_user(username='ldr', password='123')
        UserProfile.objects.create(
            user=ldr, role=Role.objects.get_or_create(name=Role.LEADER)[0], employee_id='LDR9'
        )
        data = {
            'employee_id': 'NV900', 'department': 'IT', 'position': 'Dev',
            'employee_type': 'Toàn thời gian', 'workplace': 'HN',
            'probation_start': '01/01/2026', 'official_start_date': '01/02/2026',
            'work_status': 'probation', 'manager_user': mgr.pk, 'leader_user': ldr.pk,
            'contract_number': 'HD-900', 'contract_type': 'Chính thức',
            'contract_signed_date': '01/01/2026', 'contract_start_date': '05/01/2026',
            'contract_annual_leave_days': '12', 'contract_standard_shift': '08:30-17:30',
        }
        data.update(overrides)
        return data

    def test_create_without_account_does_not_fake_success(self):
        """F1: bỏ tick tạo tài khoản → KHÔNG báo thành công giả, KHÔNG mất dữ liệu thầm lặng."""
        data = self._full_valid_payload()  # không gửi auto_create_account → off
        resp = self.client.post(self.url, data=data)
        self.assertEqual(resp.status_code, 200)
        msgs = ' '.join(self._messages(resp))
        self.assertNotIn('mô phỏng', msgs)
        self.assertNotIn('Demo', msgs)
        # Phải có hướng dẫn rõ ràng vì hồ sơ chưa được lưu.
        self.assertTrue(any('tài khoản' in m.lower() for m in self._messages(resp)))
        # Không tạo user NV900 nào (hr + mgr + ldr = 3).
        self.assertFalse(User.objects.filter(username='nv900').exists())

    def test_create_with_account_persists(self):
        """Bật tạo tài khoản → hồ sơ + account được LƯU thật."""
        data = self._full_valid_payload(auto_create_account='on')
        resp = self.client.post(self.url, data=data)
        self.assertTrue(UserProfile.objects.filter(employee_id='NV900').exists())
