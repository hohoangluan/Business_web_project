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
        # Get or create the 4 roles (the data migration may have already created them)
        self.role_master, _ = Role.objects.get_or_create(
            name='master', defaults={'description': 'Full access'}
        )
        self.role_manager, _ = Role.objects.get_or_create(
            name='manager', defaults={'description': 'Manager'}
        )
        self.role_leader, _ = Role.objects.get_or_create(
            name='leader', defaults={'description': 'Leader'}
        )
        self.role_employee, _ = Role.objects.get_or_create(
            name='employee', defaults={'description': 'Employee'}
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
            user=self.admin_user, role=self.role_master
        )

        # Create a Master-role user (not superuser, but has Master role)
        self.master_user = User.objects.create_user(
            username='master_user', password='masterpass123', email='master@example.com'
        )
        self.master_profile = UserProfile.objects.create(
            user=self.master_user, role=self.role_master
        )

        # Create a regular employee (should NOT be able to access admin pages)
        self.regular_user = User.objects.create_user(
            username='employee1', password='emppass123', email='emp@example.com'
        )
        self.regular_profile = UserProfile.objects.create(
            user=self.regular_user, role=self.role_employee
        )

        # Create a target user to assign roles/permissions to
        self.target_user = User.objects.create_user(
            username='target', password='targetpass123', email='target@example.com'
        )
        self.target_profile = UserProfile.objects.create(user=self.target_user)

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

    def test_user_list_accessible_by_master_role(self):
        """Users with the Master role SHOULD be able to see the user list."""
        self.client.login(username='master_user', password='masterpass123')
        response = self.client.get('/users/')
        self.assertEqual(response.status_code, 200)

    def test_assign_role_blocked_for_regular_user(self):
        """Regular employees should NOT be able to change roles."""
        self.client.login(username='employee1', password='emppass123')
        response = self.client.get(f'/users/{self.target_user.id}/role/')
        self.assertEqual(response.status_code, 302)

    def test_assign_permissions_blocked_for_regular_user(self):
        """Regular employees should NOT be able to change permissions."""
        self.client.login(username='employee1', password='emppass123')
        response = self.client.get(f'/users/{self.target_user.id}/permissions/')
        self.assertEqual(response.status_code, 302)

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
