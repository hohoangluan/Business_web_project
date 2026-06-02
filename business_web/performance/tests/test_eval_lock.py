"""FUNC-PER-005: đánh giá sau 'submitted' không sửa được — theo thiết kế KHÔNG có
endpoint sửa/cập nhật (chỉ tạo, duyệt-HR-acknowledge)."""
from django.test import TestCase
from django.urls import NoReverseMatch, reverse


class TestEvaluationImmutable(TestCase):
    def test_no_edit_endpoint_exists(self):
        # Không tồn tại route sửa đánh giá → đã submitted thì bất biến.
        for name in ['evaluation_edit', 'evaluation_update', 'edit_evaluation']:
            with self.assertRaises(NoReverseMatch):
                reverse(name, args=[1])

    def test_acknowledge_endpoint_exists(self):
        # Hành vi hợp lệ duy nhất sau submitted: HR acknowledge.
        self.assertTrue(reverse('evaluation_acknowledge', args=[1]))
