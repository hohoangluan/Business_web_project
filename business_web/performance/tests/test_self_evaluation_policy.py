"""Gói 4 — User không được xem phiếu đánh giá CỦA MÌNH.

Chính sách: không màn hình nào hiển thị cho người dùng đánh giá mà họ là người
ĐƯỢC đánh giá (employee == chính họ). Test khoá chính sách + guard defense-in-depth.
"""
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Role, UserProfile
from performance.services.evaluation_data import exclude_self_records


class TestExcludeSelfRecordsHelper(TestCase):
    def test_drops_records_where_viewer_is_employee(self):
        records = [
            {'employee_username': 'alice', 'content': 'x'},
            {'employee_username': 'bob', 'content': 'y'},
        ]
        result = exclude_self_records(records, 'alice')
        usernames = [r['employee_username'] for r in result]
        self.assertNotIn('alice', usernames)
        self.assertIn('bob', usernames)

    def test_empty_viewer_keeps_all(self):
        records = [{'employee_username': 'alice'}]
        self.assertEqual(len(exclude_self_records(records, '')), 1)


class TestEmployeeCannotAccessEvaluations(TestCase):
    def setUp(self):
        self.client = Client()
        self.emp_role = Role.objects.create(name=Role.EMPLOYEE)
        self.emp = User.objects.create_user(username='emp', password='123')
        UserProfile.objects.create(user=self.emp, role=self.emp_role, employee_id='E001')

    def test_employee_redirected_from_evaluations_page(self):
        """Employee mở trang đánh giá → bị chặn (redirect), không xem được gì."""
        self.client.force_login(self.emp)
        response = self.client.get(reverse('evaluations'))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('performance/evaluations.html',
                         [t.name for t in getattr(response, 'templates', [])])
