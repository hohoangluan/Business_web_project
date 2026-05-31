from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile
from employee_profiles.models import EmployeeWorkInfo
from reports_interactions.models import Report, Ticket

class TestReportsInteractions(TestCase):
    def setUp(self):
        self.client = Client()
        
        self.hr_role = Role.objects.create(name=Role.HR)
        self.mgr_role = Role.objects.create(name=Role.MANAGER)
        self.emp_role = Role.objects.create(name=Role.EMPLOYEE)
        
        self.manager = User.objects.create_user(username='manager', password='123')
        UserProfile.objects.create(user=self.manager, role=self.mgr_role, employee_id='MGR001')
        EmployeeWorkInfo.objects.create(user=self.manager, department='IT')
        
        self.employee = User.objects.create_user(username='employee', password='123')
        UserProfile.objects.create(user=self.employee, role=self.emp_role, employee_id='EMP001')
        EmployeeWorkInfo.objects.create(user=self.employee, manager_user=self.manager, department='IT')
        
        self.url_reports = reverse('reports')
        self.url_report_inbox = reverse('report_inbox')
        self.url_tickets = reverse('tickets')
        self.url_ticket_process = reverse('ticket_process')

    def test_create_report(self):
        self.client.force_login(self.employee)
        response = self.client.post(self.url_reports, data={
            'action': 'create',
            'title': 'Báo cáo tuần 1',
            'content': 'Đã hoàn thành module A',
            'recipient': self.manager.id
        })
        self.assertRedirects(response, self.url_reports)
        report = Report.objects.get(author=self.employee)
        self.assertEqual(report.title, 'Báo cáo tuần 1')
        self.assertEqual(report.recipient, self.manager)
        self.assertFalse(report.is_viewed)

    def test_edit_report(self):
        report = Report.objects.create(
            author=self.employee,
            recipient=self.manager,
            title='Old title',
            content='Old content'
        )
        self.client.force_login(self.employee)
        response = self.client.post(self.url_reports, data={
            'action': 'edit',
            'report_id': report.id,
            'title': 'New title',
            'content': 'New content',
            'recipient': self.manager.id
        })
        self.assertRedirects(response, self.url_reports)
        report.refresh_from_db()
        self.assertEqual(report.title, 'New title')
        
    def test_delete_report(self):
        report = Report.objects.create(
            author=self.employee,
            recipient=self.manager,
            title='Delete me',
            content='Delete content'
        )
        self.client.force_login(self.employee)
        response = self.client.post(self.url_reports, data={
            'action': 'delete',
            'report_id': report.id
        })
        self.assertRedirects(response, self.url_reports)
        self.assertFalse(Report.objects.filter(id=report.id).exists())

    def test_view_report_marks_as_viewed(self):
        report = Report.objects.create(
            author=self.employee,
            recipient=self.manager,
            title='Please view',
            content='Content'
        )
        self.client.force_login(self.manager)
        url = reverse('report_detail', args=[report.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        self.assertTrue(report.is_viewed)

    def test_report_inbox_access(self):
        self.client.force_login(self.manager)
        response = self.client.get(self.url_report_inbox)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reports_interactions/report_inbox.html')

    def test_create_ticket(self):
        self.client.force_login(self.employee)
        response = self.client.post(self.url_tickets, data={
            'action': 'create',
            'ticket_type': Ticket.SUPPORT,
            'priority': Ticket.PRIORITY_HIGH,
            'title': 'Lỗi đăng nhập',
            'content': 'Không thể đăng nhập vào hệ thống'
        })
        self.assertRedirects(response, self.url_tickets)
        ticket = Ticket.objects.get(author=self.employee)
        self.assertEqual(ticket.title, 'Lỗi đăng nhập')
        self.assertEqual(ticket.status, Ticket.STATUS_NEW)

    def test_process_ticket_receive(self):
        ticket = Ticket.objects.create(
            author=self.employee,
            ticket_type=Ticket.SUPPORT,
            priority=Ticket.PRIORITY_MEDIUM,
            title='Need help',
            content='Help me',
            status=Ticket.STATUS_NEW
        )
        self.client.force_login(self.manager)
        response = self.client.post(self.url_ticket_process, data={
            'action': 'receive',
            'ticket_id': ticket.id
        })
        self.assertRedirects(response, self.url_ticket_process)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, Ticket.STATUS_PROCESSING)
        self.assertEqual(ticket.assigned_to, self.manager)

    def test_process_ticket_resolve(self):
        ticket = Ticket.objects.create(
            author=self.employee,
            ticket_type=Ticket.SUPPORT,
            priority=Ticket.PRIORITY_MEDIUM,
            title='Need help',
            content='Help me',
            status=Ticket.STATUS_PROCESSING,
            assigned_to=self.manager
        )
        self.client.force_login(self.manager)
        response = self.client.post(self.url_ticket_process, data={
            'action': 'resolve',
            'ticket_id': ticket.id
        })
        self.assertRedirects(response, self.url_ticket_process)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, Ticket.STATUS_RESOLVED)

    def test_process_ticket_reject(self):
        ticket = Ticket.objects.create(
            author=self.employee,
            ticket_type=Ticket.SUPPORT,
            priority=Ticket.PRIORITY_MEDIUM,
            title='Need help',
            content='Help me',
            status=Ticket.STATUS_NEW
        )
        self.client.force_login(self.manager)
        response = self.client.post(self.url_ticket_process, data={
            'action': 'reject',
            'ticket_id': ticket.id,
            'rejection_reason': 'Not valid'
        })
        self.assertRedirects(response, self.url_ticket_process)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, Ticket.STATUS_REJECTED)
        self.assertEqual(ticket.rejection_reason, 'Not valid')
