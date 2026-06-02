"""Tests for the notification system."""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Notification
from accounts.services import create_notification

class NotificationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='employee', password='password123'
        )
        Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='This is a test notification.'
        )

    def test_notification_context_processor(self):
        self.client.login(username='employee', password='password123')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('unread_count', response.context)
        self.assertEqual(response.context['unread_count'], 1)

        # Mark as read
        notif = Notification.objects.first()
        notif.is_read = True
        notif.save()

        response = self.client.get('/dashboard/')
        self.assertEqual(response.context['unread_count'], 0)

    def test_create_notification_service(self):
        """create_notification tạo bản ghi gắn với đúng user."""
        notif = create_notification(self.user, 'Tiêu đề', 'Nội dung', link='/x/')
        self.assertIsNotNone(notif)
        self.assertEqual(notif.user, self.user)
        self.assertFalse(notif.is_read)
        self.assertEqual(notif.link, '/x/')
        # user None → bỏ qua an toàn
        self.assertIsNone(create_notification(None, 't', 'm'))

    def test_mark_read_endpoint(self):
        """POST mark-read đánh dấu mọi thông báo chưa đọc của user là đã đọc."""
        self.client.login(username='employee', password='password123')
        self.assertEqual(
            Notification.objects.filter(user=self.user, is_read=False).count(), 1
        )
        response = self.client.post(reverse('mark_notifications_read'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['updated'], 1)
        self.assertEqual(
            Notification.objects.filter(user=self.user, is_read=False).count(), 0
        )

    def test_mark_read_requires_post(self):
        self.client.login(username='employee', password='password123')
        self.assertEqual(self.client.get(reverse('mark_notifications_read')).status_code, 405)

    def test_notifications_page_marks_read(self):
        """Mở trang xem tất cả → đánh dấu đã đọc."""
        self.client.login(username='employee', password='password123')
        response = self.client.get(reverse('notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/account/notifications.html')
        self.assertEqual(
            Notification.objects.filter(user=self.user, is_read=False).count(), 0
        )
