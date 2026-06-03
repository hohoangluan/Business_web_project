"""Gói 2 — ràng buộc giờ ca HĐ: giờ kết thúc phải sau giờ bắt đầu (đồng bộ dữ liệu)."""
from django.test import TestCase

from contracts.forms import ContractAdjustForm


class TestContractShiftTimeOrder(TestCase):
    def test_shift_end_before_start_rejected(self):
        form = ContractAdjustForm(data={
            'shift_start_time': '17:30',
            'shift_end_time': '08:30',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('shift_end_time', form.errors)

    def test_shift_end_equal_start_rejected(self):
        form = ContractAdjustForm(data={
            'shift_start_time': '08:30',
            'shift_end_time': '08:30',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('shift_end_time', form.errors)

    def test_shift_end_after_start_ok(self):
        form = ContractAdjustForm(data={
            'shift_start_time': '08:30',
            'shift_end_time': '17:30',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_only_one_shift_field_does_not_crash(self):
        """Chỉ điền 1 giờ → không ràng buộc cặp, không lỗi shift."""
        form = ContractAdjustForm(data={'shift_start_time': '08:30'})
        form.is_valid()
        self.assertNotIn('shift_end_time', form.errors)
