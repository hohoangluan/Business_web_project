from django.test import TestCase
from reports_interactions.models.ticket_model import Ticket


class TicketTypeTest(TestCase):
    def test_no_timesheet_adjustment_type(self):
        labels = ' '.join(label for _, label in Ticket.TYPE_CHOICES).lower()
        self.assertNotIn('giờ công', labels)
        self.assertNotIn('điều chỉnh', labels)
