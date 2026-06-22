"""Bug #27: HR tạo hồ sơ phải validate + hiển thị lỗi giờ ca (giờ kết thúc phải sau giờ bắt đầu)."""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile


class CreateProfileShiftTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.hr_role, _ = Role.objects.get_or_create(name=Role.HR)
        self.hr = User.objects.create_user('hr_u', password='x')
        UserProfile.objects.create(user=self.hr, role=self.hr_role, employee_id='HR')
        self.client.login(username='hr_u', password='x')

    def test_bad_shift_time_shows_error(self):
        resp = self.client.post(reverse('hr_create_profile'), {
            'employee_id': 'NV9', 'department': 'X', 'position': 'Y',
            'employee_type': 'Z', 'workplace': 'W', 'work_status': 'official',
            'probation_start': '01/06/2026', 'official_start_date': '01/08/2026',
            'contract_number': 'C1', 'contract_type': 'T',
            'contract_signed_date': '01/05/2026', 'contract_start_date': '05/05/2026',
            'contract_end_date': '05/05/2027', 'contract_annual_leave_days': '12',
            'contract_standard_shift': '08:00-17:00',
            'shift_start_time': '17:00', 'shift_end_time': '08:00',
            'auto_create_account': 'on',
        }, follow=True)
        self.assertContains(resp, 'Giờ kết thúc ca')
