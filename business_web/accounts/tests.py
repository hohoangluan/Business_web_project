from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Role, CustomPermission, UserProfile


class PermissionManagementTests(TestCase):
    """
    Tests for the permission management feature.

    How Django tests work:
    - Each test method starts with a fresh, empty database (no leftover data)
    - setUp() runs BEFORE each test to create common test data
    - self.client simulates a web browser making requests
    - self.assertEqual(), self.assertTrue() etc. check if results match expectations
    - If any check fails, the test fails and tells you exactly what went wrong
    """

    def setUp(self):
        """
        Runs before EVERY test method. Creates test users and data.
        Think of this as "prepare the stage before each scene."
        """
        # Get or create the standard roles used by the current role model.
        self.role_admin, _ = Role.objects.get_or_create(
            name=Role.ADMIN, defaults={'description': 'Full access'}
        )
        self.role_hr, _ = Role.objects.get_or_create(
            name=Role.HR, defaults={'description': 'Human Resources'}
        )
        self.role_manager, _ = Role.objects.get_or_create(
            name=Role.MANAGER, defaults={'description': 'Manager'}
        )
        self.role_leader, _ = Role.objects.get_or_create(
            name=Role.LEADER, defaults={'description': 'Leader'}
        )
        self.role_employee, _ = Role.objects.get_or_create(
            name=Role.EMPLOYEE, defaults={'description': 'Employee'}
        )

        # Get or create some test permissions
        self.perm_reports, _ = CustomPermission.objects.get_or_create(
            codename='can_view_reports', defaults={'name': 'Can View Reports'}
        )
        self.perm_export, _ = CustomPermission.objects.get_or_create(
            codename='can_export_reports', defaults={'name': 'Can Export Reports'}
        )
        self.perm_team, _ = CustomPermission.objects.get_or_create(
            codename='can_manage_team', defaults={'name': 'Can Manage Team'}
        )

        # Create an admin user (superuser)
        self.admin_user = User.objects.create_superuser(
            username='admin', password='adminpass123', email='admin@example.com'
        )
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user,
            role=self.role_admin,
            full_name='System Admin',
            department='Ban điều hành',
        )

        # Create an Admin-role user (not superuser, but has Admin role)
        self.admin_role_user = User.objects.create_user(
            username='admin_role_user', password='adminrolepass123', email='adminrole@example.com'
        )
        self.admin_role_profile = UserProfile.objects.create(
            user=self.admin_role_user,
            role=self.role_admin,
            full_name='Admin Role User',
            department='Ban điều hành',
        )

        # Create an HR user for HR-only pages.
        self.hr_user = User.objects.create_user(
            username='hr1', password='hrpass123', email='hr@example.com'
        )
        self.hr_profile = UserProfile.objects.create(
            user=self.hr_user,
            role=self.role_hr,
            full_name='Ha HR',
            department='Phòng Nhân sự',
            position='HR Executive',
        )

        self.manager_user = User.objects.create_user(
            username='manager1', password='managerpass123', email='manager@example.com'
        )
        self.manager_profile = UserProfile.objects.create(
            user=self.manager_user,
            role=self.role_manager,
            full_name='Minh Manager',
            department='Khối Vận hành',
            position='Trưởng bộ phận',
        )

        self.leader_user = User.objects.create_user(
            username='leader1', password='leaderpass123', email='leader@example.com'
        )
        self.leader_profile = UserProfile.objects.create(
            user=self.leader_user,
            role=self.role_leader,
            full_name='Lan Leader',
            department='Khối Vận hành',
            position='Team Leader',
            manager_user=self.manager_user,
        )

        # Create a regular employee (should NOT be able to access admin pages)
        self.regular_user = User.objects.create_user(
            username='employee1', password='emppass123', email='employee1@gmail.com'
        )
        self.regular_profile = UserProfile.objects.create(
            user=self.regular_user,
            role=self.role_employee,
            full_name='Nam Employee',
            department='Khối Vận hành',
            position='Nhân viên vận hành',
            manager_user=self.manager_user,
            leader_user=self.leader_user,
        )

        self.outside_user = User.objects.create_user(
            username='employee2', password='employee2pass123', email='employee2@gmail.com'
        )
        self.outside_profile = UserProfile.objects.create(
            user=self.outside_user,
            role=self.role_employee,
            full_name='Hoa Outside',
            department='Khối Kinh doanh',
            position='Nhân viên kinh doanh',
        )

        # Create a target user to assign roles/permissions to
        self.target_user = User.objects.create_user(
            username='target', password='targetpass123', email='target@example.com'
        )
        self.target_profile = UserProfile.objects.create(
            user=self.target_user,
            role=self.role_employee,
            full_name='Target User',
            department='Khối Hỗ trợ',
            position='Nhân viên hỗ trợ',
        )

        # Django test client — simulates a web browser
        self.client = Client()

    # =========================================================================
    # ACCESS CONTROL TESTS
    # These test that only authorized users can access admin pages
    # =========================================================================

    def test_user_list_blocked_for_regular_user(self):
        """Regular employees should NOT be able to see the user list."""
        self.client.login(username='employee1', password='emppass123')
        response = self.client.get('/users/')
        # 302 = redirect (to login page), meaning access was denied
        self.assertEqual(response.status_code, 302)

    def test_user_list_blocked_for_anonymous(self):
        """Users who aren't logged in should NOT see the user list."""
        response = self.client.get('/users/')
        self.assertEqual(response.status_code, 302)

    def test_user_list_accessible_by_superuser(self):
        """Superusers SHOULD be able to see the user list."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get('/users/')
        self.assertEqual(response.status_code, 200)

    def test_user_list_accessible_by_admin_role(self):
        """Users with the Admin role SHOULD be able to see the user list."""
        self.client.login(username='admin_role_user', password='adminrolepass123')
        response = self.client.get('/users/')
        self.assertEqual(response.status_code, 200)

    def test_user_list_accessible_by_hr(self):
        """HR should be able to open the organization management page."""
        self.client.login(username='hr1', password='hrpass123')
        response = self.client.get('/users/')
        self.assertEqual(response.status_code, 200)

    def test_assign_role_blocked_for_regular_user(self):
        """Regular employees should NOT be able to change roles."""
        self.client.login(username='employee1', password='emppass123')
        response = self.client.get(f'/users/{self.target_user.id}/role/')
        self.assertEqual(response.status_code, 302)

    def test_work_info_page_accessible_by_hr(self):
        """HR should be able to edit work info."""
        self.client.login(username='hr1', password='hrpass123')
        response = self.client.get(f'/users/{self.target_user.id}/work-info/')
        self.assertEqual(response.status_code, 200)

    def test_work_info_saves_correctly(self):
        """Submitting the HR edit form should update all stored profile fields."""
        self.client.login(username='hr1', password='hrpass123')
        response = self.client.post(
            f'/users/{self.target_user.id}/work-info/',
            {
                'full_name': 'Target Updated',
                'email': 'target-updated@example.com',
                'phone_number': '0911222333',
                'date_of_birth': '10/10/1998',
                'employee_id': 'EMP-TARGET-NEW',
                'department': 'Khối Sản phẩm',
                'employee_type': 'Toàn thời gian',
                'position': 'Business Analyst',
                'workplace': 'Văn phòng Hồ Chí Minh',
                'probation_start': '01/06/2026',
                'official_start_date': '01/08/2026',
                'work_status': 'working',
                'manager_user': self.manager_user.id,
                'leader_user': self.leader_user.id,
            }
        )
        self.assertEqual(response.status_code, 302)
        self.target_user.refresh_from_db()
        self.target_profile.refresh_from_db()
        self.assertEqual(self.target_profile.full_name, 'Target Updated')
        self.assertEqual(self.target_user.email, 'target-updated@example.com')
        self.assertEqual(self.target_profile.phone_number, '0911222333')
        self.assertEqual(self.target_profile.date_of_birth, '10/10/1998')
        self.assertEqual(self.target_profile.employee_id, 'EMP-TARGET-NEW')
        self.assertEqual(self.target_profile.department, 'Khối Sản phẩm')
        self.assertEqual(self.target_profile.employee_type, 'Toàn thời gian')
        self.assertEqual(self.target_profile.position, 'Business Analyst')
        self.assertEqual(self.target_profile.workplace, 'Văn phòng Hồ Chí Minh')
        self.assertEqual(self.target_profile.probation_start, '01/06/2026')
        self.assertEqual(self.target_profile.official_start_date, '01/08/2026')
        self.assertEqual(self.target_profile.work_status, 'working')
        self.assertEqual(self.target_profile.manager_user, self.manager_user)
        self.assertEqual(self.target_profile.leader_user, self.leader_user)

    def test_hr_create_profile_allows_blank_personal_info_when_work_info_present(self):
        """HR can create a profile with required work info even if personal info is blank."""
        self.client.login(username='hr1', password='hrpass123')
        response = self.client.post(
            '/hr/create-profile/',
            {
                'full_name': '',
                'email': '',
                'phone_number': '',
                'date_of_birth': '',
                'employee_id': 'NV900',
                'department': 'Khối Vận hành',
                'employee_type': 'Toàn thời gian',
                'position': 'Chuyên viên vận hành',
                'workplace': 'Văn phòng Hà Nội',
                'probation_start': '01/05/2026',
                'official_start_date': '01/07/2026',
                'work_status': 'working',
                'manager_user': self.manager_user.id,
                'leader_user': self.leader_user.id,
                'role': 'employee',
                'auto_create_account': 'on',
            }
        )
        self.assertEqual(response.status_code, 302)
        new_user = User.objects.get(username='nv900')
        self.assertEqual(new_user.email, '')
        self.assertEqual(new_user.profile.full_name, '')
        self.assertEqual(new_user.profile.employee_id, 'NV900')
        self.assertEqual(new_user.profile.department, 'Khối Vận hành')
        self.assertEqual(new_user.profile.employee_type, 'Toàn thời gian')
        self.assertEqual(new_user.profile.position, 'Chuyên viên vận hành')
        self.assertEqual(new_user.profile.workplace, 'Văn phòng Hà Nội')
        self.assertEqual(new_user.profile.probation_start, '01/05/2026')
        self.assertEqual(new_user.profile.official_start_date, '01/07/2026')
        self.assertEqual(new_user.profile.work_status, 'working')
        self.assertEqual(new_user.profile.manager_user, self.manager_user)
        self.assertEqual(new_user.profile.leader_user, self.leader_user)

    def test_assign_permissions_blocked_for_regular_user(self):
        """Regular employees should NOT be able to change permissions."""
        self.client.login(username='employee1', password='emppass123')
        response = self.client.get(f'/users/{self.target_user.id}/permissions/')
        self.assertEqual(response.status_code, 302)

    def test_employee_does_not_see_manager_action_buttons(self):
        """Employees should not see approval/management buttons after login."""
        self.client.login(username='employee1', password='emppass123')

        self.assert_manager_action_buttons_hidden()

    def test_superuser_switched_to_employee_does_not_see_manager_action_buttons(self):
        """The dev role switcher should let superusers preview Employee UI."""
        self.admin_profile.role = self.role_employee
        self.admin_profile.save()
        self.client.login(username='admin', password='adminpass123')

        self.assert_manager_action_buttons_hidden()

    def assert_manager_action_buttons_hidden(self):
        hidden_buttons_by_path = {
            '/leave/': ['Đi đến Trang Phê duyệt'],
            '/overtime/': ['Đi đến Trang Phê duyệt'],
            '/reports/': ['Xem Hộp thư Báo cáo'],
            '/tickets/': ['Trang Xử lý Ticket'],
            '/rewards-penalties/': ['Phê duyệt Phiếu'],
        }

        for path, hidden_buttons in hidden_buttons_by_path.items():
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                for button_text in hidden_buttons:
                    self.assertNotContains(response, button_text)

    def test_employee_cannot_access_manager_action_urls_directly(self):
        """Employees should be redirected away from approval/management URLs."""
        self.client.login(username='employee1', password='emppass123')

        self.assert_manager_action_urls_redirect()

    def test_superuser_switched_to_employee_cannot_access_manager_urls_directly(self):
        """A superuser switched to Employee should be blocked from business actions."""
        self.admin_profile.role = self.role_employee
        self.admin_profile.save()
        self.client.login(username='admin', password='adminpass123')

        self.assert_manager_action_urls_redirect()

    def assert_manager_action_urls_redirect(self):
        protected_urls = [
            '/leave/approval/',
            '/overtime/approval/',
            '/reports/inbox/',
            '/tickets/process/',
            '/rewards-penalties/approval/',
        ]

        for path in protected_urls:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 302)

    def test_statistics_accessible_by_hr(self):
        """HR users should be able to access the statistics page."""
        self.client.login(username='hr1', password='hrpass123')
        response = self.client.get('/statistics/')
        self.assertEqual(response.status_code, 200)

    def test_statistics_accessible_by_superuser(self):
        """Superusers should be able to access the statistics page."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get('/statistics/')
        self.assertEqual(response.status_code, 200)

    def test_statistics_accessible_by_manager(self):
        """Managers should be able to access the statistics page."""
        self.client.login(username='manager1', password='managerpass123')
        response = self.client.get('/statistics/')
        self.assertEqual(response.status_code, 200)

    def test_statistics_accessible_by_leader(self):
        """Leaders should be able to access the statistics page."""
        self.client.login(username='leader1', password='leaderpass123')
        response = self.client.get('/statistics/')
        self.assertEqual(response.status_code, 200)

    def test_statistics_blocked_for_employee(self):
        """Employees should not be able to access the statistics page."""
        self.client.login(username='employee1', password='emppass123')
        response = self.client.get('/statistics/')
        self.assertEqual(response.status_code, 302)

    def test_hr_dashboard_shows_statistics_button(self):
        """HR users should see the statistics shortcut on the dashboard."""
        self.client.login(username='hr1', password='hrpass123')
        response = self.client.get('/dashboard/')
        self.assertContains(response, 'Statistics')

    def test_manager_statistics_scope_hides_other_departments(self):
        """Managers should only see employees from their own department."""
        self.client.login(username='manager1', password='managerpass123')
        response = self.client.get('/statistics/')
        self.assertContains(response, 'Nam Employee')
        self.assertNotContains(response, 'Hoa Outside')

    def test_leader_statistics_scope_hides_other_departments(self):
        """Leaders should only see employees assigned to their team."""
        self.client.login(username='leader1', password='leaderpass123')
        response = self.client.get('/statistics/')
        self.assertContains(response, 'Nam Employee')
        self.assertNotContains(response, 'Hoa Outside')

    def test_statistics_export_csv_respects_scope(self):
        """CSV export should follow the same scope as the statistics page."""
        self.client.login(username='manager1', password='managerpass123')
        response = self.client.get('/statistics/export-csv/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8-sig')
        self.assertIn('Nam Employee', content)
        self.assertNotIn('Hoa Outside', content)

    def test_payroll_routes_return_404(self):
        """Legacy payroll URLs should no longer exist."""
        self.client.login(username='admin', password='adminpass123')
        for path in ['/payroll/', '/payroll/calc/', '/payroll/approval/']:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 404)

    def test_settings_company_profile_visible_for_admin_role(self):
        """Only the active Admin role should see the company profile settings."""
        self.client.login(username='admin_role_user', password='adminrolepass123')
        response = self.client.get('/settings/')
        self.assertContains(response, 'Hồ sơ Công ty')
        self.assertContains(response, 'Hồ sơ Doanh nghiệp')

    def test_settings_company_profile_hidden_for_employee_and_hr(self):
        """Employee and HR roles should not see the company profile settings."""
        users = [
            ('employee1', 'emppass123'),
            ('hr1', 'hrpass123'),
        ]

        for username, password in users:
            with self.subTest(username=username):
                self.client.logout()
                self.client.login(username=username, password=password)
                response = self.client.get('/settings/')
                self.assertNotContains(response, 'Hồ sơ Công ty')
                self.assertNotContains(response, 'Hồ sơ Doanh nghiệp')

    def test_settings_company_profile_hidden_for_superuser_switched_to_employee(self):
        """The dev role switcher should hide company settings in Employee mode."""
        self.admin_profile.role = self.role_employee
        self.admin_profile.save()
        self.client.login(username='admin', password='adminpass123')

        response = self.client.get('/settings/')
        self.assertNotContains(response, 'Hồ sơ Công ty')
        self.assertNotContains(response, 'Hồ sơ Doanh nghiệp')

    def test_settings_hr_panel_shows_standard_shift_end_time_field(self):
        """HR should see the standard shift end time field in settings."""
        self.client.login(username='hr1', password='hrpass123')
        response = self.client.get('/settings/')
        self.assertContains(response, 'Giờ kết thúc ca làm chuẩn')

    def test_profile_page_hides_bank_and_tax_tab(self):
        """The personal profile page should no longer show the bank/tax section."""
        self.client.login(username='employee1', password='emppass123')
        response = self.client.get('/profile/')
        self.assertNotContains(response, 'Ngân hàng & Thuế')

    # =========================================================================
    # USER LIST TESTS
    # =========================================================================

    def test_user_list_shows_all_users(self):
        """The user list page should show all users in the system."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get('/users/')
        content = response.content.decode()
        # Check that each user's username appears on the page
        self.assertIn('admin', content)
        self.assertIn('employee1', content)
        self.assertIn('target', content)

    # =========================================================================
    # ROLE ASSIGNMENT TESTS
    # =========================================================================

    def test_assign_role_page_loads(self):
        """The assign role page should load and show the form."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(f'/users/{self.target_user.id}/role/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('target', response.content.decode())

    def test_assign_role_saves_correctly(self):
        """Submitting the role form should update the user's role."""
        self.client.login(username='admin', password='adminpass123')
        # POST the form with the manager role ID
        self.client.post(
            f'/users/{self.target_user.id}/role/',
            {'role': self.role_manager.id}
        )
        # Reload the profile from the database and check
        self.target_profile.refresh_from_db()
        self.assertEqual(self.target_profile.role, self.role_manager)

    def test_assign_role_does_not_change_permissions(self):
        """Changing a role should NOT affect the user's permissions."""
        # First, give the target user a permission
        self.target_profile.permissions.add(self.perm_reports)

        self.client.login(username='admin', password='adminpass123')
        # Change the role
        self.client.post(
            f'/users/{self.target_user.id}/role/',
            {'role': self.role_leader.id}
        )

        # Check: role changed, but permission is still there
        self.target_profile.refresh_from_db()
        self.assertEqual(self.target_profile.role, self.role_leader)
        self.assertTrue(
            self.target_profile.permissions.filter(codename='can_view_reports').exists()
        )

    # =========================================================================
    # PERMISSION ASSIGNMENT TESTS
    # =========================================================================

    def test_assign_permissions_page_loads(self):
        """The assign permissions page should load and show checkboxes."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(f'/users/{self.target_user.id}/permissions/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('target', response.content.decode())

    def test_assign_permissions_saves_correctly(self):
        """Submitting the permissions form should update the user's permissions."""
        self.client.login(username='admin', password='adminpass123')
        # Give the user two permissions
        self.client.post(
            f'/users/{self.target_user.id}/permissions/',
            {'permissions': [self.perm_reports.id, self.perm_export.id]}
        )
        # Check: user now has exactly those two permissions
        self.target_profile.refresh_from_db()
        perms = list(self.target_profile.permissions.values_list('codename', flat=True))
        self.assertIn('can_view_reports', perms)
        self.assertIn('can_export_reports', perms)
        self.assertEqual(len(perms), 2)

    def test_assign_permissions_does_not_change_role(self):
        """Changing permissions should NOT affect the user's role."""
        # Set a role first
        self.target_profile.role = self.role_employee
        self.target_profile.save()

        self.client.login(username='admin', password='adminpass123')
        # Change permissions
        self.client.post(
            f'/users/{self.target_user.id}/permissions/',
            {'permissions': [self.perm_team.id]}
        )

        # Check: permissions changed, but role is still Employee
        self.target_profile.refresh_from_db()
        self.assertEqual(self.target_profile.role, self.role_employee)

    def test_clear_all_permissions(self):
        """Submitting with no checkboxes checked should remove all permissions."""
        # Give the user a permission first
        self.target_profile.permissions.add(self.perm_reports)

        self.client.login(username='admin', password='adminpass123')
        # POST without selecting any permissions
        self.client.post(
            f'/users/{self.target_user.id}/permissions/',
            {'permissions': []}
        )

        # Check: all permissions should be removed
        self.target_profile.refresh_from_db()
        self.assertEqual(self.target_profile.permissions.count(), 0)

    # =========================================================================
    # EDGE CASES
    # =========================================================================

    def test_invalid_user_returns_404(self):
        """Trying to manage a non-existent user should return 404."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get('/users/99999/role/')
        self.assertEqual(response.status_code, 404)

    def test_invalid_user_permissions_returns_404(self):
        """Trying to manage permissions for a non-existent user should return 404."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get('/users/99999/permissions/')
        self.assertEqual(response.status_code, 404)

    def test_has_custom_permission_helper(self):
        """The has_custom_permission() helper method should work correctly."""
        self.target_profile.permissions.add(self.perm_reports)
        self.assertTrue(self.target_profile.has_custom_permission('can_view_reports'))
        self.assertFalse(self.target_profile.has_custom_permission('can_export_reports'))

    def test_register_creates_profile(self):
        """Registering a new user should create a UserProfile with all fields."""
        response = self.client.post('/register/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'StrongPass!234',
            'password2': 'StrongPass!234',
            'full_name': 'Nguyen Van A',
            'phone_number': '0901234567',
            'date_of_birth': '15/06/1990',
            'employee_id': 'EMP999',
        })
        self.assertEqual(response.status_code, 302)
        new_user = User.objects.get(username='newuser')
        self.assertTrue(hasattr(new_user, 'profile'))
        self.assertEqual(new_user.profile.full_name, 'Nguyen Van A')
        self.assertEqual(new_user.profile.phone_number, '0901234567')
        self.assertEqual(new_user.profile.date_of_birth, '15/06/1990')
        self.assertEqual(new_user.profile.employee_id, 'EMP999')

    # =========================================================================
    # REGISTRATION VALIDATION TESTS
    # =========================================================================

    def test_register_full_name_no_numbers(self):
        """Full Name must not contain numbers."""
        response = self.client.post('/register/', {
            'username': 'testval1', 'email': 'x@y.com',
            'password1': 'StrongPass!234', 'password2': 'StrongPass!234',
            'full_name': 'Nguyen 123', 'phone_number': '0901234567',
            'date_of_birth': '01/01/2000', 'employee_id': 'VAL001',
        })
        self.assertEqual(response.status_code, 200)  # stays on page (error)
        self.assertFalse(User.objects.filter(username='testval1').exists())

    def test_register_email_must_have_at(self):
        """Email must contain @."""
        response = self.client.post('/register/', {
            'username': 'testval2', 'email': 'invalid-email',
            'password1': 'StrongPass!234', 'password2': 'StrongPass!234',
            'full_name': 'Valid Name', 'phone_number': '0901234567',
            'date_of_birth': '01/01/2000', 'employee_id': 'VAL002',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='testval2').exists())

    def test_register_phone_digits_only(self):
        """Phone number must contain digits only."""
        response = self.client.post('/register/', {
            'username': 'testval3', 'email': 'x@y.com',
            'password1': 'StrongPass!234', 'password2': 'StrongPass!234',
            'full_name': 'Valid Name', 'phone_number': '090-abc',
            'date_of_birth': '01/01/2000', 'employee_id': 'VAL003',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='testval3').exists())

    def test_register_dob_format(self):
        """Date of birth must be DD/MM/YYYY."""
        response = self.client.post('/register/', {
            'username': 'testval4', 'email': 'x@y.com',
            'password1': 'StrongPass!234', 'password2': 'StrongPass!234',
            'full_name': 'Valid Name', 'phone_number': '0901234567',
            'date_of_birth': '2000-01-01', 'employee_id': 'VAL004',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='testval4').exists())

    def test_register_employee_id_unique(self):
        """Employee ID must be unique — can't reuse an existing one."""
        # target_profile already has employee_id, set one
        self.target_profile.employee_id = 'EMP_TAKEN'
        self.target_profile.save()

        response = self.client.post('/register/', {
            'username': 'testval5', 'email': 'x@y.com',
            'password1': 'StrongPass!234', 'password2': 'StrongPass!234',
            'full_name': 'Valid Name', 'phone_number': '0901234567',
            'date_of_birth': '01/01/2000', 'employee_id': 'EMP_TAKEN',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='testval5').exists())

    def test_login_only_needs_username_password(self):
        """Login should work with just username and password."""
        response = self.client.post('/login/', {
            'username': 'employee1',
            'password': 'emppass123',
        })
        self.assertEqual(response.status_code, 302)  # redirect to dashboard

    def test_login_page_links_to_forgot_password(self):
        """Login page should link to the password recovery UI."""
        response = self.client.get('/login/')
        self.assertContains(response, '/forgot-password/')
        self.assertContains(response, 'Quên mật khẩu?')

    def test_forgot_password_page_loads_username_step(self):
        """Password recovery starts with the username step."""
        response = self.client.get('/forgot-password/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nhập username')
        self.assertContains(response, 'Gửi mã xác nhận')

    def test_forgot_password_username_submit_shows_code_step(self):
        """Submitting a valid username should show the verification code UI."""
        response = self.client.post('/forgot-password/', {
            'step': 'username',
            'username': 'employee1',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Xác nhận mã')
        self.assertContains(response, 'e*******1@gmail.com')

    def test_forgot_password_unknown_username_shows_error(self):
        """Unknown usernames should stay on the recovery UI with an error."""
        response = self.client.post('/forgot-password/', {
            'step': 'username',
            'username': 'missing_user',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Không tìm thấy tài khoản')

    # =========================================================================
    # DELETE USER TESTS
    # =========================================================================

    def test_delete_user_blocked_for_regular_user(self):
        """Regular employees should NOT be able to delete users."""
        self.client.login(username='employee1', password='emppass123')
        response = self.client.get(f'/users/{self.target_user.id}/delete/')
        self.assertEqual(response.status_code, 302)

    def test_delete_user_confirmation_page(self):
        """GET request shows confirmation page."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(f'/users/{self.target_user.id}/delete/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('target', response.content.decode())

    def test_delete_user_works(self):
        """POST request deletes the user."""
        self.client.login(username='admin', password='adminpass123')
        target_id = self.target_user.id
        response = self.client.post(f'/users/{target_id}/delete/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(id=target_id).exists())

    def test_cannot_delete_self(self):
        """Admin cannot delete their own account."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(f'/users/{self.admin_user.id}/delete/')
        self.assertEqual(response.status_code, 302)  # redirected
        self.assertTrue(User.objects.filter(id=self.admin_user.id).exists())
