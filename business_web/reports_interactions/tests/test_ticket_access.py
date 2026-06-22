from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile


class TicketAccessTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.mgr_role, _ = Role.objects.get_or_create(name=Role.MANAGER)
        self.mgr = User.objects.create_user('mgr', password='x')
        UserProfile.objects.create(user=self.mgr, role=self.mgr_role, employee_id='M1')

    def test_manager_blocked_from_ticket_process(self):
        self.client.login(username='mgr', password='x')
        resp = self.client.get(reverse('ticket_process'), follow=True)
        self.assertContains(resp, 'không có quyền')
