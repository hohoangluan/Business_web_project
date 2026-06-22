from django.test import SimpleTestCase
from contracts.services import validate_work_date_order


class WorkDateOrderTest(SimpleTestCase):
    def test_probation_after_official_rejected(self):
        errs = validate_work_date_order('01/09/2026', '01/08/2026')
        self.assertTrue(errs)

    def test_probation_before_official_ok(self):
        self.assertEqual(validate_work_date_order('01/06/2026', '01/08/2026'), [])
