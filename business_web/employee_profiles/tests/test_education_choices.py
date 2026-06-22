from django.test import SimpleTestCase
from employee_profiles.forms import EmployeeProfileForm, EDUCATION_LEVEL_CHOICES


class EducationChoiceTest(SimpleTestCase):
    def test_education_level_is_choice_field(self):
        form = EmployeeProfileForm()
        widget = form.fields['education_level'].widget.__class__.__name__
        self.assertEqual(widget, 'Select')
        labels = [label for _, label in EDUCATION_LEVEL_CHOICES]
        self.assertIn('THPT', labels)
        self.assertIn('Đại học', labels)
