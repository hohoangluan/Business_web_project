"""python manage.py close_open_attendance [--cutoff YYYY-MM-DD]

Stamps `status='no_checkout'` on every AttendanceRecord with check_in_time
set, check_out_time NULL, and record_date < cutoff (default: today).
Idempotent.
"""
from datetime import datetime, date

from django.core.management.base import BaseCommand
from django.utils import timezone

from attendance.services.record.attendance_logging_service import close_open_records_before


class Command(BaseCommand):
    help = "Close attendance records that have a check-in but no check-out, before --cutoff."

    def add_arguments(self, parser):
        parser.add_argument(
            '--cutoff', type=str, default=None,
            help='YYYY-MM-DD. Default: today (localdate).',
        )

    def handle(self, *args, **options):
        if options['cutoff']:
            cutoff = datetime.strptime(options['cutoff'], '%Y-%m-%d').date()
        else:
            cutoff = timezone.localdate()
        affected = close_open_records_before(cutoff)
        self.stdout.write(
            f'Closed {affected} open record(s) before {cutoff.isoformat()}.'
        )
