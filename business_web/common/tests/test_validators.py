from django.test import SimpleTestCase
from django.core.exceptions import ValidationError
from common.validators import validate_phone_number


class PhoneValidatorTest(SimpleTestCase):
    def test_rejects_letters(self):
        with self.assertRaises(ValidationError):
            validate_phone_number('09abc1234x')

    def test_rejects_wrong_length(self):
        with self.assertRaises(ValidationError):
            validate_phone_number('012')

    def test_accepts_valid(self):
        self.assertEqual(validate_phone_number('0901234567'), '0901234567')

    def test_blank_allowed(self):
        self.assertEqual(validate_phone_number(''), '')
