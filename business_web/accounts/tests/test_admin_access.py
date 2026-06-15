"""Admin chỉ quản lý hệ thống — bị chặn khỏi mọi chức năng nghiệp vụ."""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from accounts.models import Role, UserProfile


BUSINESS_VIEWS = [
    'profile', 'contract', 'attendance', 'leave',
    'overtime', 'reports', 'rewards_penalties',
]


class AdminAccessTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_role, _ = Role.objects.get_or_create(name=Role.ADMIN)
        self.emp_role, _ = Role.objects.get_or_create(name=Role.EMPLOYEE)
        self.hr_role, _ = Role.objects.get_or_create(name=Role.HR)
        self.manager_role, _ = Role.objects.get_or_create(name=Role.MANAGER)
        self.leader_role, _ = Role.objects.get_or_create(name=Role.LEADER)

        self.admin = User.objects.create_user('admin_u', password='x')
        UserProfile.objects.create(user=self.admin, role=self.admin_role, employee_id='ADM')
        self.hr = User.objects.create_user('hr_u', password='x')
        UserProfile.objects.create(user=self.hr, role=self.hr_role, employee_id='HR')
        self.manager = User.objects.create_user('mgr_u', password='x')
        UserProfile.objects.create(user=self.manager, role=self.manager_role, employee_id='MGR')
        self.leader = User.objects.create_user('lead_u', password='x')
        UserProfile.objects.create(user=self.leader, role=self.leader_role, employee_id='LEAD')

    def test_is_admin_property(self):
        self.assertTrue(self.admin.profile.is_admin)
        self.assertFalse(self.hr.profile.is_admin)

    def test_admin_blocked_from_business_views(self):
        self.client.force_login(self.admin)
        for name in BUSINESS_VIEWS:
            resp = self.client.get(reverse(name))
            self.assertEqual(resp.status_code, 302, f'{name} phải chặn admin')
            self.assertEqual(resp.headers['Location'], reverse('dashboard'))

    def test_admin_blocked_from_eval_and_stats_views(self):
        """Admin bị chặn khỏi trang đánh giá, xác nhận đánh giá và thống kê."""
        self.client.force_login(self.admin)
        for name in ['statistics', 'evaluations', 'evaluation_hr_approval']:
            resp = self.client.get(reverse(name))
            self.assertEqual(resp.status_code, 302, f'{name} phải chặn admin')
            self.assertEqual(resp.headers['Location'], reverse('dashboard'))

    def test_admin_permission_flags_for_eval_and_stats(self):
        """Admin không có quyền xem/xác nhận đánh giá và xem thống kê."""
        from accounts.services import (
            can_acknowledge_evaluation, can_access_statistics,
            can_access_evaluations,
        )
        self.assertFalse(can_access_evaluations(self.admin))
        self.assertFalse(can_acknowledge_evaluation(self.admin))
        self.assertFalse(can_access_statistics(self.admin))
        # HR vẫn xác nhận được đánh giá.
        self.assertTrue(can_acknowledge_evaluation(self.hr))

    def test_admin_stripped_from_all_business_processes(self):
        """Admin chỉ giữ kênh hỗ trợ (ticket); gỡ mọi phê duyệt/yêu cầu nhân sự."""
        from accounts.services import can_manage_requests, can_process_tickets
        from rewards_discipline.services import _is_l1_approver, _is_l2_approver
        from attendance.services.face.face_change_service import _is_trusted

        # Admin: gỡ hết nghiệp vụ nhân sự (phê duyệt / yêu cầu).
        self.assertFalse(can_manage_requests(self.admin))
        self.assertFalse(_is_l1_approver(self.admin))
        self.assertFalse(_is_l2_approver(self.admin))
        self.assertFalse(_is_trusted(self.admin))
        # Admin: GIỮ kênh hỗ trợ (xử lý ticket).
        self.assertTrue(can_process_tickets(self.admin))
        # HR vẫn đủ quyền nghiệp vụ + hỗ trợ.
        self.assertTrue(can_manage_requests(self.hr))
        self.assertTrue(_is_l2_approver(self.hr))
        self.assertTrue(_is_trusted(self.hr))
        self.assertTrue(can_process_tickets(self.hr))
        # Quản lý/Leader: duyệt nghiệp vụ NHƯNG không xử lý ticket.
        self.assertTrue(can_manage_requests(self.manager))
        self.assertTrue(can_manage_requests(self.leader))
        self.assertFalse(can_process_tickets(self.manager))
        self.assertFalse(can_process_tickets(self.leader))

    def test_admin_ticket_support_views(self):
        """Admin vào được trang xử lý ticket; bị chặn khỏi hộp thư báo cáo nhân sự."""
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('ticket_process')).status_code, 200)
        self.assertEqual(self.client.get(reverse('tickets')).status_code, 200)
        self.assertEqual(self.client.get(reverse('report_inbox')).status_code, 302)

    def test_hr_can_view_rewards(self):
        """HR phải xem được Khen thưởng & Xử phạt."""
        self.client.force_login(self.hr)
        self.assertEqual(self.client.get(reverse('rewards_penalties')).status_code, 200)

    def test_hr_can_view_profile(self):
        self.client.force_login(self.hr)
        self.assertEqual(self.client.get(reverse('profile')).status_code, 200)

    def test_admin_create_account_username_password(self):
        """Admin tạo tài khoản chỉ với username + password; giữ phiên admin."""
        self.client.force_login(self.admin)
        resp = self.client.post(reverse('admin_create_account'), {
            'username': 'newacc',
            'password': 'Str0ngPass!23',
            'password_confirm': 'Str0ngPass!23',
        })
        self.assertRedirects(resp, reverse('user_list'))
        self.assertTrue(User.objects.filter(username='newacc').exists())
        # Vẫn là phiên admin (không tự đăng nhập vào tài khoản mới).
        self.assertEqual(self.client.get(reverse('dashboard')).wsgi_request.user, self.admin)

    def test_admin_create_account_rejects_mismatch_and_weak(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('admin_create_account'), {
            'username': 'mm', 'password': 'Str0ngPass!23', 'password_confirm': 'other',
        })
        self.assertFalse(User.objects.filter(username='mm').exists())
        self.client.post(reverse('admin_create_account'), {
            'username': 'weak', 'password': '123', 'password_confirm': '123',
        })
        self.assertFalse(User.objects.filter(username='weak').exists())

    def test_non_admin_cannot_create_account(self):
        self.client.force_login(self.hr)
        self.assertEqual(self.client.get(reverse('admin_create_account')).status_code, 302)

    def test_superuser_role_simulation(self):
        """DEV: superuser mô phỏng role nào thì xem giao diện + quyền của role đó.

        - Chưa gán role → dev/admin (chặn nghiệp vụ, vào được quản lý hệ thống).
        - Mô phỏng employee → xem hồ sơ, bị chặn khen thưởng.
        - Mô phỏng HR → xem được khen thưởng.
        """
        su = User.objects.create_superuser('dev_u', 'd@x.com', 'x')
        UserProfile.objects.create(user=su, employee_id='DEV')
        self.client.force_login(su)

        # Mặc định (chưa role) = admin/dev.
        self.assertTrue(User.objects.get(pk=su.pk).profile.is_admin)
        self.assertEqual(self.client.get(reverse('rewards_penalties')).status_code, 302)

        # Mô phỏng employee.
        self.client.post(reverse('switch_role'), {'role_name': Role.EMPLOYEE})
        self.assertFalse(User.objects.get(pk=su.pk).profile.is_admin)
        self.assertEqual(self.client.get(reverse('profile')).status_code, 200)
        self.assertEqual(self.client.get(reverse('rewards_penalties')).status_code, 302)

        # Mô phỏng HR.
        self.client.post(reverse('switch_role'), {'role_name': Role.HR})
        self.assertEqual(self.client.get(reverse('rewards_penalties')).status_code, 200)
