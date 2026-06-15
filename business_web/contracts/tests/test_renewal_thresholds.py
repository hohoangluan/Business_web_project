"""FUNC-CON-008: phân loại cảnh báo hết hạn HĐ — biên 7 (khẩn) / 30 (xa)."""
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from contracts.models import ContractInfo
from contracts.services import expire_overdue_contracts, get_expiring_contracts


class TestRenewalThresholds(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='nv', password='123')
        self.today = timezone.localdate()

    def _contract(self, days_from_now, number):
        end = self.today + timedelta(days=days_from_now)
        return ContractInfo.objects.create(
            user=self.user, is_active=True, contract_number=number,
            contract_type='CT', contract_signed_date='01/01/2026',
            contract_start_date='01/01/2026',
            contract_end_date=end.strftime('%d/%m/%Y'),
            contract_annual_leave_days=12, contract_standard_shift='08:30-17:30',
        )

    def test_threshold_classification(self):
        self._contract(7, 'C7')    # khẩn (<=7)
        self._contract(8, 'C8')    # mốc lẻ → không xuất hiện
        self._contract(15, 'C15')  # xa (mốc 15)
        self._contract(30, 'C30')  # xa (biên trên)
        self._contract(31, 'C31')  # ngoài ngưỡng → không xuất hiện

        results = get_expiring_contracts(days_threshold=30)
        by_num = {r['contract'].contract_number: r['urgency'] for r in results}

        self.assertEqual(by_num.get('C7'), 'near')
        self.assertNotIn('C8', by_num)   # 8 ngày không phải mốc → loại
        self.assertEqual(by_num.get('C15'), 'far')  # mốc 15 → xa
        self.assertEqual(by_num.get('C30'), 'far')
        self.assertNotIn('C31', by_num)  # >30 ngày → loại

    def test_expired_not_listed(self):
        self._contract(-1, 'CEXP')  # đã hết hạn
        results = get_expiring_contracts(days_threshold=30)
        self.assertNotIn('CEXP', {r['contract'].contract_number for r in results})


class TestExpireOverdueContracts(TestCase):
    """FUNC-CON-008 (F6): HĐ quá hạn → tự is_active=False."""

    def setUp(self):
        self.user = User.objects.create_user(username='nv', password='123')
        self.today = timezone.localdate()

    def _contract(self, days_from_now, number):
        end = self.today + timedelta(days=days_from_now)
        return ContractInfo.objects.create(
            user=self.user, is_active=True, contract_number=number,
            contract_type='CT', contract_signed_date='01/01/2026',
            contract_start_date='01/01/2026',
            contract_end_date=end.strftime('%d/%m/%Y'),
            contract_annual_leave_days=12, contract_standard_shift='08:30-17:30',
        )

    def test_overdue_set_inactive(self):
        past = self._contract(-1, 'CPAST')
        future = self._contract(10, 'CFUT')
        n = expire_overdue_contracts()
        self.assertEqual(n, 1)
        past.refresh_from_db()
        future.refresh_from_db()
        self.assertFalse(past.is_active)   # quá hạn → hết hiệu lực
        self.assertTrue(future.is_active)  # còn hạn → giữ nguyên

    def test_open_ended_kept_active(self):
        c = ContractInfo.objects.create(
            user=self.user, is_active=True, contract_number='CNOEND',
            contract_type='CT', contract_signed_date='01/01/2026',
            contract_start_date='01/01/2026', contract_end_date='',
            contract_annual_leave_days=12, contract_standard_shift='08:30-17:30',
        )
        expire_overdue_contracts()
        c.refresh_from_db()
        self.assertTrue(c.is_active)  # không thời hạn → không đụng
