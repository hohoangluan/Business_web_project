"""Gói 2 — HR cấu hình giờ làm qua panel tab-hr của trang Settings."""
from datetime import time

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Role, UserProfile
from attendance.models import WorkScheduleConfig


class TestWorkScheduleSettings(TestCase):
    def setUp(self):
        self.client = Client()
        self.settings_url = reverse('settings')

        self.hr = User.objects.create_user(username='hr001', password='Password123!')
        hr_role, _ = Role.objects.get_or_create(name=Role.HR)
        hr_profile, _ = UserProfile.objects.get_or_create(
            user=self.hr, defaults={'employee_id': 'HR001'}
        )
        hr_profile.role = hr_role
        hr_profile.save()

        self.employee = User.objects.create_user(username='nv001', password='Password123!')
        UserProfile.objects.get_or_create(
            user=self.employee, defaults={'employee_id': 'NV001'}
        )

    def test_hr_can_save_work_schedule(self):
        """HR POST hợp lệ → WorkScheduleConfig được cập nhật."""
        self.client.force_login(self.hr)
        response = self.client.post(self.settings_url, data={
            'form_section': 'work_schedule',
            'shift_start': '09:00',
            'shift_end': '18:00',
            'late_grace_minutes': '10',
        })
        self.assertEqual(response.status_code, 200)
        config = WorkScheduleConfig.get_solo()
        self.assertEqual(config.shift_start, time(9, 0))
        self.assertEqual(config.shift_end, time(18, 0))
        self.assertEqual(config.late_grace_minutes, 10)

    def test_hr_invalid_end_before_start_shows_error(self):
        """HR POST giờ ra <= giờ vào → không lưu + hiện lỗi."""
        self.client.force_login(self.hr)
        response = self.client.post(self.settings_url, data={
            'form_section': 'work_schedule',
            'shift_start': '17:00',
            'shift_end': '08:00',
            'late_grace_minutes': '5',
        })
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('Giờ kết thúc phải sau giờ bắt đầu', content)
        config = WorkScheduleConfig.get_solo()
        # Giữ mặc định, không lưu giá trị sai.
        self.assertEqual(config.shift_start, time(8, 30))

    def test_employee_cannot_change_work_schedule(self):
        """Nhân viên thường POST → cấu hình không đổi (bị chặn)."""
        self.client.force_login(self.employee)
        self.client.post(self.settings_url, data={
            'form_section': 'work_schedule',
            'shift_start': '06:00',
            'shift_end': '23:00',
            'late_grace_minutes': '99',
        })
        config = WorkScheduleConfig.get_solo()
        self.assertEqual(config.shift_start, time(8, 30))
        self.assertEqual(config.late_grace_minutes, 5)

    def test_hr_get_shows_current_values(self):
        """GET trang settings (HR) → panel hiện giá trị giờ hiện tại."""
        config = WorkScheduleConfig.get_solo()
        config.shift_start = time(7, 45)
        config.save()
        self.client.force_login(self.hr)
        response = self.client.get(self.settings_url)
        self.assertContains(response, '07:45')
