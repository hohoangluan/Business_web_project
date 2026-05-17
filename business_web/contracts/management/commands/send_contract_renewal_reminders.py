"""
==============================================================================
Management Command: send_contract_renewal_reminders
==============================================================================
Quet toan bo hop dong sap het han va gui email nhac nho den:
  - Nhan vien co hop dong sap het han
  - Manager va Leader phu trach nhan vien do
  - Tat ca HR trong he thong

Cach dung:
  python manage.py send_contract_renewal_reminders
  python manage.py send_contract_renewal_reminders --days=30
  python manage.py send_contract_renewal_reminders --dry-run

Tich hop Windows Task Scheduler de chay luc 0h00 moi ngay.
==============================================================================
"""

from django.core.management.base import BaseCommand
from contracts.services.renewal_service import (
    THRESHOLD_FAR,
    THRESHOLD_NEAR,
    get_expiring_contracts,
    get_recipients_for_contract,
)
from contracts.services.email_service import send_renewal_reminder_email


class Command(BaseCommand):
    help = (
        "Gui email nhac gia han hop dong cho cac hop dong sap het han "
        "(nguong mac dinh: 30 ngay va 7 ngay)"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=THRESHOLD_FAR,
            help=f"So ngay toi da de coi la 'sap het han' (mac dinh: {THRESHOLD_FAR})",
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help="Chi xem danh sach, khong gui email that",
        )

    def handle(self, *args, **options):
        import sys
        # Fix encoding cho Windows console (cp1252 -> utf-8)
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8')
            except Exception:
                pass

        days    = options['days']
        dry_run = options['dry_run']

        sep = '=' * 60
        self.stdout.write(sep)
        self.stdout.write("  Contract Renewal Reminder")
        self.stdout.write(f"  Nguong: {days} ngay | Khan: {THRESHOLD_NEAR} ngay")
        mode = "DRY-RUN (khong gui email)" if dry_run else "GUI THAT"
        self.stdout.write(f"  Che do: {mode}")
        self.stdout.write(sep)

        expiring = get_expiring_contracts(days_threshold=days)

        if not expiring:
            self.stdout.write(self.style.SUCCESS(
                "Khong co hop dong nao sap het han trong nguong da chi dinh."
            ))
            return

        near_group = [e for e in expiring if e['urgency'] == 'near']
        far_group  = [e for e in expiring if e['urgency'] == 'far']

        self.stdout.write(f"\nTim thay {len(expiring)} hop dong sap het han:")
        self.stdout.write(f"  * Khan cap (<= {THRESHOLD_NEAR} ngay): {len(near_group)}")
        self.stdout.write(f"  * Som    (<= {days} ngay): {len(far_group)}")

        success_count = 0
        fail_count    = 0

        for item in expiring:
            contract  = item['contract']
            days_left = item['days_left']
            urgency   = item['urgency']
            employee  = contract.user

            profile   = getattr(employee, 'profile', None)
            full_name = getattr(profile, 'full_name', '') or employee.username
            emp_id    = getattr(profile, 'employee_id', '') or '--'

            urgency_tag = f"[KHAN - {days_left} ngay]" if urgency == 'near' else f"[{days_left} ngay]"

            self.stdout.write(f"\n  {urgency_tag} {full_name} ({emp_id})")
            self.stdout.write(
                f"           HD: {contract.contract_number or '--'} "
                f"| Het han: {contract.contract_end_date}"
            )

            recipients = get_recipients_for_contract(contract)
            recip_str = ', '.join(recipients) if recipients else 'Khong co email'
            self.stdout.write(f"           Nguoi nhan: {recip_str}")

            if dry_run:
                self.stdout.write("           -> DRY-RUN: bo qua gui email.")
                continue

            if not recipients:
                self.stdout.write("           -> Bo qua: khong co dia chi email.")
                fail_count += 1
                continue

            ok = send_renewal_reminder_email(contract, recipients, days_left)
            if ok:
                self.stdout.write(self.style.SUCCESS("           -> Da gui email thanh cong."))
                success_count += 1
            else:
                self.stdout.write(self.style.ERROR("           -> Gui email that bai."))
                fail_count += 1

        self.stdout.write(f"\n{sep}")
        if dry_run:
            self.stdout.write(
                f"DRY-RUN hoan tat. {len(expiring)} hop dong se duoc nhac khi chay that."
            )
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Hoan tat: {success_count} thanh cong, {fail_count} that bai."
            ))
        self.stdout.write(f"{sep}\n")
