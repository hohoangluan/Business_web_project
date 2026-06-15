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


class TestAcknowledgeGuard(TestCase):
    """acknowledge_evaluation chỉ duyệt phiếu đang 'submitted' (khớp ST-EVAL)."""

    def setUp(self):
        from django.contrib.auth.models import User
        self.hr = User.objects.create_user('hr_ack', password='x')
        self.emp = User.objects.create_user('emp_ack', password='x')
        self.rev = User.objects.create_user('rev_ack', password='x')

    def _make(self, status):
        from datetime import date
        from performance.models import Evaluation
        return Evaluation.objects.create(
            employee=self.emp, reviewer=self.rev, status=status,
            evaluation_date=date.today(), content='x',
        )

    def test_acknowledge_submitted_ok(self):
        from performance.services import acknowledge_evaluation
        ev = self._make('submitted')
        ok, _ = acknowledge_evaluation(self.hr, ev.id, 'note')
        self.assertTrue(ok)
        ev.refresh_from_db()
        self.assertEqual(ev.status, 'acknowledged')
        self.assertEqual(ev.acknowledged_by, self.hr)

    def test_acknowledge_rejects_non_submitted(self):
        from performance.services import acknowledge_evaluation
        for status in ['draft', 'acknowledged']:
            ev = self._make(status)
            ok, _ = acknowledge_evaluation(self.hr, ev.id, 'note')
            self.assertFalse(ok, f'status={status} không được acknowledge')
            ev.refresh_from_db()
            self.assertEqual(ev.status, status)
