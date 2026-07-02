from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import CompanyConfiguration, Role, UserProfile
from contracts.forms import ContractAdjustForm
from employee_profiles.forms import EmployeeProfileForm


class CompanyConfigurationSettingsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.settings_url = reverse('settings')
        self.admin_role, _ = Role.objects.get_or_create(name=Role.ADMIN)
        self.hr_role, _ = Role.objects.get_or_create(name=Role.HR)

        self.admin = User.objects.create_user('admin_config', password='Password123!')
        UserProfile.objects.create(user=self.admin, role=self.admin_role, employee_id='ADMCFG')

        self.hr = User.objects.create_user('hr_config', password='Password123!')
        UserProfile.objects.create(user=self.hr, role=self.hr_role, employee_id='HRCFG')

    def _payload(self):
        return {
            'form_section': 'company_configuration',
            'workplaces': 'Hà Nội HQ\nRemote\nRemote',
            'contract_types': 'Chính thức 1 năm\nCộng tác viên',
            'reward_policy': 'Thưởng KPI cuối quý.',
            'penalty_policy': 'Phạt vi phạm nội quy đã xác minh.',
            'departments': 'Sản phẩm\nChăm sóc khách hàng',
            'positions': 'Product Owner\nChuyên viên CSKH',
        }

    def test_admin_can_update_company_configuration(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.settings_url, data=self._payload())

        self.assertEqual(response.status_code, 200)
        config = CompanyConfiguration.get_solo()
        self.assertEqual(config.workplaces, 'Hà Nội HQ\nRemote')
        self.assertEqual(config.contract_types, 'Chính thức 1 năm\nCộng tác viên')
        self.assertEqual(config.reward_policy, 'Thưởng KPI cuối quý.')
        self.assertEqual(config.penalty_policy, 'Phạt vi phạm nội quy đã xác minh.')
        self.assertEqual(config.departments, 'Sản phẩm\nChăm sóc khách hàng')
        self.assertEqual(config.positions, 'Product Owner\nChuyên viên CSKH')

    def test_non_admin_cannot_update_company_configuration(self):
        config = CompanyConfiguration.get_solo()
        original_departments = config.departments

        self.client.force_login(self.hr)
        response = self.client.post(self.settings_url, data=self._payload())

        self.assertEqual(response.status_code, 200)
        config.refresh_from_db()
        self.assertEqual(config.departments, original_departments)

    def test_company_configuration_drives_profile_and_contract_choices(self):
        config = CompanyConfiguration.get_solo()
        config.departments = 'R&D'
        config.positions = 'Solution Architect'
        config.workplaces = 'Đà Lạt Office'
        config.contract_types = 'Hợp đồng chuyên gia'
        config.save()

        profile_form = EmployeeProfileForm()
        contract_form = ContractAdjustForm()

        self.assertIn(('R&D', 'R&D'), profile_form.fields['department'].choices)
        self.assertIn(('Solution Architect', 'Solution Architect'), profile_form.fields['position'].choices)
        self.assertIn(('Đà Lạt Office', 'Đà Lạt Office'), profile_form.fields['workplace'].choices)
        self.assertIn(('Hợp đồng chuyên gia', 'Hợp đồng chuyên gia'), contract_form.fields['contract_type'].choices)
