from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import RegisterForm, AssignRoleForm, AssignPermissionsForm
from .models import UserProfile


# =============================================================================
# HELPER: Access Control Check
# =============================================================================

def is_admin_user(user):
    """
    Check if the logged-in user is allowed to manage other users.
    Returns True if the user is a superuser OR has the 'Master' role.

    This function is used with @user_passes_test decorator:
      - If True → the user can access the page
      - If False → the user is redirected to the login page
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        return user.profile.is_master()
    except UserProfile.DoesNotExist:
        return False


def ensure_profile(user):
    """
    Make sure a user has a UserProfile.
    If they don't (e.g., they were created before we added profiles),
    create one automatically.
    """
    profile, created = UserProfile.objects.get_or_create(user=user)
    return profile


# =============================================================================
# PUBLIC VIEWS: Registration, Login, Logout, Dashboard
# =============================================================================

def register_view(request):
    """
    Handles user registration with 7 fields.
    - GET request: shows the registration form
    - POST request: validates, creates user + profile, then logs them in
    """
    if request.user.is_authenticated:
        return redirect('dashboard') 
    # 1. Look for name = 'dashboard' in urls.py
    # 2. Call dashboard_view in views.py
    # 3. return render(request, 'accounts/dashboard.html')
    # 4. render the template 'accounts/dashboard.html' in templates/accounts/dashboard.html to have frontend

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()           # Save user (username, email, password)

            # Create UserProfile with the extra registration fields
            profile = ensure_profile(user)
            profile.full_name = form.cleaned_data['full_name']
            profile.phone_number = form.cleaned_data['phone_number']
            profile.date_of_birth = form.cleaned_data['date_of_birth']
            profile.employee_id = form.cleaned_data['employee_id']
            profile.save()

            login(request, user)         # Auto-login after registration
            return redirect('dashboard')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def dashboard_view(request):
    """
    The main page users see after logging in.
    Shows different content based on the user's role.
    """
    ensure_profile(request.user)
    return render(request, 'accounts/dashboard.html')


def logout_view(request):
    """Logs the user out and redirects to the login page."""
    logout(request)
    return redirect('login')


# =============================================================================
# ADMIN VIEWS: User Management (only for Master / superuser)
# =============================================================================
# These views are protected by @user_passes_test(is_admin_user).
# If a non-admin tries to access them, they get redirected to the login page.
# =============================================================================

@login_required
@user_passes_test(is_admin_user)
def user_list_view(request):
    """
    Shows a list of ALL users in the system.
    Displays: username, email, role, permissions count, and action links.

    Only accessible by Master/superuser.
    """
    users = User.objects.all().select_related('profile__role').prefetch_related(
        'profile__permissions'
    )

    # Ensure every user has a profile (handles legacy users)
    for user in users:
        ensure_profile(user)

    return render(request, 'accounts/user_list.html', {'users': users})


@login_required
@user_passes_test(is_admin_user)
def assign_role_view(request, user_id):
    """
    Form to change a specific user's ROLE.

    How it works:
    1. Admin visits /users/5/role/ → sees a dropdown with 4 roles
    2. Admin picks a role and clicks "Save"
    3. The user's profile is updated with the new role
    4. A success message is shown

    Changing the role does NOT affect the user's permissions.
    """
    # get_object_or_404: finds the user by ID, or returns a 404 error page
    target_user = get_object_or_404(User, pk=user_id)
    profile = ensure_profile(target_user)

    if request.method == 'POST':
        form = AssignRoleForm(request.POST)
        if form.is_valid():
            profile.role = form.cleaned_data['role']
            profile.save()
            messages.success(
                request,
                f"Role for '{target_user.username}' updated to "
                f"'{profile.role}' successfully."
                if profile.role else
                f"Role removed from '{target_user.username}'."
            )
            return redirect('user_list')
    else:
        # Pre-fill the form with the user's current role
        form = AssignRoleForm(initial={'role': profile.role})

    return render(request, 'accounts/assign_role.html', {
        'form': form,
        'target_user': target_user,
    })


@login_required
@user_passes_test(is_admin_user)
def assign_permissions_view(request, user_id):
    """
    Form to assign/remove PERMISSIONS for a specific user.

    How it works:
    1. Admin visits /users/5/permissions/ → sees checkboxes for all permissions
    2. Checked = user has the permission; unchecked = user doesn't
    3. Admin clicks "Save" → permissions are updated
    4. A success message is shown

    Changing permissions does NOT affect the user's role.
    """
    target_user = get_object_or_404(User, pk=user_id)
    profile = ensure_profile(target_user)

    if request.method == 'POST':
        form = AssignPermissionsForm(request.POST)
        if form.is_valid():
            # .set() replaces ALL current permissions with the selected ones.
            # If nothing is checked, all permissions are removed.
            profile.permissions.set(form.cleaned_data['permissions'])
            messages.success(
                request,
                f"Permissions for '{target_user.username}' updated successfully."
            )
            return redirect('user_list')
    else:
        # Pre-fill the form with the user's current permissions
        form = AssignPermissionsForm(
            initial={'permissions': profile.permissions.all()}
        )

    return render(request, 'accounts/assign_permissions.html', {
        'form': form,
        'target_user': target_user,
    })


@login_required
@user_passes_test(is_admin_user)
def delete_user_view(request, user_id):
    """
    Delete a user account. Only superusers/Master can do this.

    How it works:
    1. GET request → shows a confirmation page ("Are you sure?")
    2. POST request → actually deletes the user and redirects to the user list
    3. You CANNOT delete yourself (safety check)
    """
    target_user = get_object_or_404(User, pk=user_id)

    # Safety: don't let admins delete themselves
    if target_user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('user_list')

    if request.method == 'POST':
        username = target_user.username
        target_user.delete()  # This also deletes the UserProfile (CASCADE)
        messages.success(request, f"User '{username}' has been deleted.")
        return redirect('user_list')

    return render(request, 'accounts/delete_user.html', {
        'target_user': target_user,
    })