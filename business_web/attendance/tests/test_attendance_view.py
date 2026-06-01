from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from attendance.models import AttendanceRecord

class TestAttendanceView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='nv001', password='123')
        
        # Tạo 2 bản ghi trong THÁNG HIỆN TẠI (neo theo đầu tháng để không phụ
        # thuộc ngày chạy test — view chỉ hiển thị record từ đầu tháng trở đi).
        first_of_month = timezone.localdate().replace(day=1)
        AttendanceRecord.objects.create(
            user=self.user,
            record_date=first_of_month,
            check_in_time=timezone.now().replace(hour=8, minute=0, second=0, microsecond=0),
            check_out_time=timezone.now().replace(hour=17, minute=0, second=0, microsecond=0),
            status='present'
        )

        AttendanceRecord.objects.create(
            user=self.user,
            record_date=first_of_month + timedelta(days=1),
            check_in_time=timezone.now().replace(hour=8, minute=30, second=0, microsecond=0),
            status='late'
        )
        
        self.url = reverse('attendance')
        
    def test_att_view_01_view_records(self):
        """ATT-VIEW-01: Employee xem trang chấm công"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'attendance/record/attendance.html')
        self.assertContains(response, 'badge-ontime')
        self.assertContains(response, 'badge-late')
        
    def test_att_view_02_data_correctness(self):
        """ATT-VIEW-02: Kiểm tra dữ liệu records hiển thị đúng"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        records = response.context['history_rows']
        self.assertEqual(len(records), 2)
        
    def test_att_view_03_require_login(self):
        """Check require login"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)


class TestShiftClassify(TestCase):
    def test_classify_status(self):
        from datetime import time
        from attendance.services.record.attendance_logging_service import classify_status
        ss, se = time(8, 30), time(17, 30)
        self.assertEqual(classify_status(time(8, 30), time(17, 30), ss, se), 'on_time')
        self.assertEqual(classify_status(time(9, 0), time(17, 30), ss, se), 'late')
        self.assertEqual(classify_status(time(8, 30), time(16, 0), ss, se), 'early_leave')
        self.assertEqual(classify_status(time(8, 30), None, ss, se), 'on_time')

    def test_get_shift_times_fallback(self):
        from django.contrib.auth.models import User
        from contracts.services import get_shift_times
        from django.conf import settings
        u = User.objects.create_user('noshift', password='1')
        start, end = get_shift_times(u)
        self.assertEqual(start, settings.WORK_START_TIME)
        self.assertEqual(end, settings.WORK_END_TIME)
