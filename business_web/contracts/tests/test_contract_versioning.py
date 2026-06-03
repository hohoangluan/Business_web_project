"""Test versioning hợp đồng: adjust_contract + get_contract_history."""
from django.test import TestCase
from django.contrib.auth.models import User

from contracts.models import ContractInfo
from contracts.services import adjust_contract, get_contract_history
from accounts.services import ensure_contract_info
from contracts.forms import ContractAdjustForm


class AdjustContractTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='nv001', password='x')
        contract = ensure_contract_info(self.user)
        contract.contract_number = 'HD-2026-001'
        contract.contract_type = 'Thử việc 2 tháng'
        contract.contract_annual_leave_days = 12
        contract.save()

    def test_adjust_creates_new_active_and_archives_old(self):
        adjust_contract(self.user, {'contract_type': 'Chính thức 1 năm'})
        contracts = ContractInfo.objects.filter(user=self.user)
        self.assertEqual(contracts.count(), 2)
        self.assertEqual(contracts.filter(is_active=True).count(), 1)
        self.assertEqual(contracts.filter(is_active=False).count(), 1)

    def test_unchanged_fields_carry_forward(self):
        new = adjust_contract(self.user, {'contract_type': 'Chính thức 1 năm'})
        self.assertEqual(new.contract_type, 'Chính thức 1 năm')   # field sửa
        self.assertEqual(new.contract_number, 'HD-2026-001')      # carry-forward
        self.assertEqual(new.contract_annual_leave_days, 12)      # carry-forward
        self.assertTrue(new.is_active)

    def test_ensure_contract_info_returns_new_version(self):
        new = adjust_contract(self.user, {'contract_number': 'HD-2026-002'})
        self.assertEqual(ensure_contract_info(self.user).pk, new.pk)

    def test_history_lists_all_newest_first(self):
        adjust_contract(self.user, {'contract_number': 'HD-2026-002'})
        history = list(get_contract_history(self.user))
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].contract_number, 'HD-2026-002')  # mới nhất trước
        self.assertEqual(history[1].contract_number, 'HD-2026-001')


class ContractAdjustFormTests(TestCase):
    BASE = {
        'contract_number': 'HD-2026-001',
        'contract_type': 'Chính thức',
        'contract_signed_date': '01/05/2026',
        'contract_start_date': '05/05/2026',
        'contract_end_date': '05/05/2027',
        'contract_annual_leave_days': 12,
        'contract_standard_shift': '08:30 - 17:30',
        'contract_attachment_reference': '',
    }

    def test_valid_form(self):
        self.assertTrue(ContractAdjustForm(data=self.BASE).is_valid())

    def test_bad_date_format_invalid(self):
        data = {**self.BASE, 'contract_signed_date': '2026-05-01'}
        form = ContractAdjustForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('contract_signed_date', form.errors)

    def test_wrong_date_order_invalid(self):
        data = {**self.BASE, 'contract_start_date': '01/04/2026'}  # trước ngày ký
        form = ContractAdjustForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('contract_start_date', form.errors)
