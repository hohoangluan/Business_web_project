"""Regression lock: Admin tạo tài khoản rồi đổi role không bị "bay" phiên (#13, #14).

`admin_create_account_view` (URL name `admin_create_account`) không gọi
`login(request, new_user)` — nó chỉ tạo user mới và redirect về `user_list`,
giữ nguyên phiên đăng nhập của Admin. Các test dưới đây khoá hành vi đó lại
để tránh hồi quy.
"""

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Role, UserProfile


class AdminCreateSessionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_role, _ = Role.objects.get_or_create(name=Role.ADMIN)
        self.admin = User.objects.create_user("admin_u", password="Password@123")
        UserProfile.objects.create(
            user=self.admin, role=self.admin_role, employee_id="ADM"
        )

    def test_admin_stays_logged_in_after_creating_account(self):
        """Admin tạo tài khoản mới -> vẫn là Admin đăng nhập, không bị đổi sang user mới."""
        self.client.login(username="admin_u", password="Password@123")

        self.client.post(
            reverse("admin_create_account"),
            {
                "username": "newbie",
                "password": "Password@123",
                "password_confirm": "Password@123",
            },
        )

        # Phiên hiện tại vẫn thuộc về admin_u, không bị chuyển sang newbie.
        self.assertEqual(
            int(self.client.session["_auth_user_id"]), self.admin.id
        )
        self.assertTrue(User.objects.filter(username="newbie").exists())

    def test_role_change_keeps_admin_authenticated(self):
        """Sau khi tạo tài khoản, Admin (superuser) đổi role -> vẫn còn đăng nhập."""
        superadmin = User.objects.create_superuser(
            "super_admin", password="Password@123"
        )
        UserProfile.objects.create(
            user=superadmin, role=self.admin_role, employee_id="SUPER"
        )

        self.client.login(username="super_admin", password="Password@123")

        self.client.post(
            reverse("admin_create_account"),
            {
                "username": "newbie2",
                "password": "Password@123",
                "password_confirm": "Password@123",
            },
        )

        response = self.client.post(
            reverse("switch_role"), {"role_name": Role.MANAGER}
        )

        login_url = reverse("login")
        self.assertNotIn(login_url, response.get("Location", ""))
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(
            int(self.client.session["_auth_user_id"]), superadmin.id
        )
