"""
Views cho hồ sơ cá nhân và quản lý hồ sơ nhân sự (HR/Admin).
"""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User

from accounts.models import UserProfile, Role
from common.file_validation import validate_upload
from employee_profiles.models import EmployeeDocument
from accounts.services import (
    ensure_profile, ensure_work_info, ensure_contract_info,
    ensure_personal_info, ensure_emergency_contact, ensure_education_info,
    is_admin_user, is_hr_user, can_manage_work_info, create_notification,
)
from employee_profiles.forms import (
    EmployeeProfileForm, PersonalEditForm, MAJOR_SUGGESTIONS, EDUCATION_LEVEL_CHOICES,
)
from employee_profiles.services import (
    get_manager_user_queryset, get_leader_user_queryset,
    build_hr_create_profile_context,
    save_work_info_from_data, save_contract_info_from_data,
    save_personal_info_from_data, save_emergency_contact_from_data, save_education_info_from_data,
)


def email_is_used_by_other_user(email, user=None):
    """Return whether an optional email already belongs to another account."""

    email = (email or '').strip()
    if not email:
        return False

    user_queryset = User.objects.filter(email__iexact=email)
    if user:
        user_queryset = user_queryset.exclude(pk=user.pk)
    return user_queryset.exists()


@login_required
def profile_view(request):
    """
    Trang hồ sơ cá nhân.
    - GET: hiển thị thông tin
    - POST: cập nhật thông tin cá nhân cơ bản
    Template: employee_profiles/profile.html
    """
    if is_admin_user(request.user):
        messages.error(request, 'Tài khoản Admin không sử dụng hồ sơ cá nhân.')
        return redirect('dashboard')

    profile = ensure_profile(request.user)
    ensure_work_info(request.user)
    ensure_contract_info(request.user)
    ensure_personal_info(request.user)
    ensure_emergency_contact(request.user)
    ensure_education_info(request.user)

    if request.method == 'POST':
        form = PersonalEditForm(request.POST, instance_user=request.user)

        if form.is_valid():
            full_name = form.cleaned_data['full_name']
            email = form.cleaned_data['email']
            phone_number = form.cleaned_data['phone_number']
            date_of_birth = form.cleaned_data['date_of_birth']
            email_changed = email != (request.user.email or '')

            # Lưu mọi thay đổi trong 1 transaction → all-or-nothing,
            # không lưu nửa vời nếu một bước lỗi giữa chừng.
            with transaction.atomic():
                profile.full_name = full_name
                if email_changed:
                    request.user.email = email
                    request.user.save(update_fields=['email'])
                profile.save()

                personal_info = ensure_personal_info(request.user)
                if phone_number:
                    personal_info.phone_number = phone_number
                if date_of_birth:
                    personal_info.date_of_birth = date_of_birth
                personal_info.save()

                # Lưu các thông tin mở rộng khác từ POST
                save_personal_info_from_data(request.user, request.POST)
                save_emergency_contact_from_data(request.user, request.POST)
                save_education_info_from_data(request.user, request.POST)

            messages.success(request, 'Cập nhật hồ sơ thành công!')
            return redirect('profile')

        # Form không hợp lệ → hiển thị lỗi từng field thay vì redirect âm thầm.
        return render(request, 'employee_profiles/profile.html', {
            'form': form,
            'active_page': 'profile',
            'major_suggestions': MAJOR_SUGGESTIONS,
            'education_level_choices': EDUCATION_LEVEL_CHOICES,
        })

    return render(request, 'employee_profiles/profile.html', {
        'active_page': 'profile',
        'major_suggestions': MAJOR_SUGGESTIONS,
        'education_level_choices': EDUCATION_LEVEL_CHOICES,
    })


@login_required
def upload_document_view(request):
    """
    Xử lý tải lên tệp minh chứng cho nhân viên.
    """
    if request.method == 'POST' and request.FILES.get('file'):
        title = request.POST.get('title', 'Tài liệu mới').strip()
        doc_type = request.POST.get('document_type', '').strip()
        file = request.FILES.get('file')

        try:
            validate_upload(file)  # 5 MB + PDF/JPG/PNG
        except ValidationError as exc:
            messages.error(request, ' '.join(exc.messages))
            return redirect('profile')

        EmployeeDocument.objects.create(
            user=request.user,
            title=title,
            document_type=doc_type,
            file=file
        )
        messages.success(request, 'Tải lên tài liệu thành công!')
    else:
        messages.error(request, 'Vui lòng chọn tệp để tải lên.')

    return redirect('profile')


@login_required
@user_passes_test(can_manage_work_info)
def hr_view_profile_view(request, user_id):
    """
    HR/Admin xem chi tiết đầy đủ hồ sơ nhân viên (chỉ đọc).
    Hiển thị toàn bộ: thông tin cá nhân, công việc, hợp đồng,
    liên hệ khẩn cấp, học vấn, tài liệu đính kèm.
    Template: employee_profiles/hr_view_profile.html
    """
    if is_admin_user(request.user):
        messages.error(request, 'Tài khoản Admin không có quyền xem chi tiết hồ sơ nhân sự.')
        return redirect('user_list')

    target_user = get_object_or_404(User, pk=user_id)
    profile = ensure_profile(target_user)
    work_info = ensure_work_info(target_user)
    contract_info = ensure_contract_info(target_user)
    personal_info = ensure_personal_info(target_user)
    emergency_contact = ensure_emergency_contact(target_user)
    education_info = ensure_education_info(target_user)
    documents = EmployeeDocument.objects.filter(user=target_user)

    return render(request, 'employee_profiles/hr_view_profile.html', {
        'target_user': target_user,
        'profile': profile,
        'work_info': work_info,
        'contract_info': contract_info,
        'personal_info': personal_info,
        'emergency_contact': emergency_contact,
        'education_info': education_info,
        'documents': documents,
        'active_page': 'users',
        'can_manage_system_users': is_admin_user(request.user),
        'can_manage_work_info': can_manage_work_info(request.user),
    })


@login_required
@user_passes_test(is_hr_user)
def hr_create_profile_view(request):
    """
    HR tạo hồ sơ nhân viên mới.
    - GET: hiển thị form
    - POST: tạo User + UserProfile + EmployeeWorkInfo + ContractInfo
    Template: employee_profiles/hr_create_profile.html
    """
    ensure_profile(request.user)

    if request.method == 'POST':
        # Đọc dữ liệu từ form
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone_number', '').strip()
        dob = request.POST.get('date_of_birth', '').strip()
        employee_id = request.POST.get('employee_id', '').strip()
        employee_type = request.POST.get('employee_type', '').strip()
        department = request.POST.get('department', '').strip()
        position = request.POST.get('position', '').strip()
        workplace = request.POST.get('workplace', '').strip()
        probation_start = request.POST.get('probation_start', '').strip()
        official_start_date = request.POST.get('official_start_date', '').strip()
        contract_number = request.POST.get('contract_number', '').strip()
        contract_type = request.POST.get('contract_type', '').strip()
        contract_signed_date = request.POST.get('contract_signed_date', '').strip()
        contract_start_date = request.POST.get('contract_start_date', '').strip()
        contract_end_date = request.POST.get('contract_end_date', '').strip()
        contract_annual_leave_days_raw = request.POST.get('contract_annual_leave_days', '').strip()
        contract_standard_shift = request.POST.get('contract_standard_shift', '').strip()
        contract_attachment_reference = request.POST.get('contract_attachment_reference', '').strip()
        work_status = request.POST.get('work_status', '').strip()
        manager_user_id = request.POST.get('manager_user', '').strip()
        leader_user_id = request.POST.get('leader_user', '').strip()
        role_name = request.POST.get('role', '').strip()
        auto_create = request.POST.get('auto_create_account') == 'on'

        manager_user = User.objects.filter(pk=manager_user_id).first() if manager_user_id else None
        leader_user = User.objects.filter(pk=leader_user_id).first() if leader_user_id else None
        contract_annual_leave_days = None

        # Validation
        errors = []
        if not employee_id:
            errors.append('Mã nhân viên không được để trống.')
        elif UserProfile.objects.filter(employee_id=employee_id).exists():
            errors.append(f'Mã nhân viên "{employee_id}" đã tồn tại.')
        if email_is_used_by_other_user(email):
            errors.append('Email này đã được sử dụng.')
        if not department:
            errors.append('Phòng ban không được để trống.')
        if not position:
            errors.append('Chức vụ không được để trống.')
        if not employee_type:
            errors.append('Loại nhân viên không được để trống.')
        if not workplace:
            errors.append('Nơi làm việc không được để trống.')
        if not probation_start:
            errors.append('Ngày bắt đầu thử việc không được để trống.')
        if not official_start_date:
            errors.append('Ngày làm việc chính thức không được để trống.')
        if not work_status:
            errors.append('Trạng thái làm việc không được để trống.')
        # manager_user / leader_user là tùy chọn: có thể để trống 1 hoặc cả 2.
        # Định tuyến phê duyệt khi thiếu quản lý xử lý ở leaves/overtime services.
        if not contract_number:
            errors.append('Số hợp đồng không được để trống.')
        if not contract_type:
            errors.append('Loại hợp đồng không được để trống.')
        if not contract_signed_date:
            errors.append('Ngày ký hợp đồng không được để trống.')
        if not contract_start_date:
            errors.append('Ngày bắt đầu hiệu lực không được để trống.')
        if not contract_annual_leave_days_raw:
            errors.append('Số ngày nghỉ phép/năm không được để trống.')
        else:
            try:
                contract_annual_leave_days = int(contract_annual_leave_days_raw)
                if contract_annual_leave_days < 0:
                    errors.append('Số ngày nghỉ phép/năm phải từ 0 trở lên.')
            except ValueError:
                errors.append('Số ngày nghỉ phép/năm phải là số nguyên.')
        if not contract_standard_shift:
            errors.append('Ca làm tiêu chuẩn không được để trống.')

        # Ràng buộc thứ tự ngày HĐ (BĐ ≥ ký, hết hạn ≥ BĐ).
        from contracts.services import validate_contract_date_order
        errors.extend(validate_contract_date_order(
            contract_signed_date, contract_start_date, contract_end_date,
        ))

        # Ràng buộc ngày thử việc ≤ ngày chính thức.
        from contracts.services import validate_work_date_order
        errors.extend(validate_work_date_order(probation_start, official_start_date))

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(
                request,
                'employee_profiles/hr_create_profile.html',
                build_hr_create_profile_context(request.POST),
            )

        if auto_create:
            username = employee_id.lower().replace(' ', '')
            password = f'{employee_id}@2026'

            if User.objects.filter(username=username).exists():
                messages.error(request, f'Username "{username}" đã tồn tại.')
                return render(
                    request,
                    'employee_profiles/hr_create_profile.html',
                    build_hr_create_profile_context(request.POST),
                )

            # Tạo User + Profile
            user = User.objects.create_user(username=username, email=email, password=password)
            profile = ensure_profile(user)
            profile.employee_id = employee_id
            profile.full_name = full_name
            if role_name:
                role, _ = Role.objects.get_or_create(name=role_name)
                profile.role = role
            profile.save()

            # Save basic personal info
            personal_info = ensure_personal_info(user)
            personal_info.phone_number = phone
            personal_info.date_of_birth = dob
            personal_info.save()

            # Lưu thông tin công việc
            save_work_info_from_data(user, {
                'employee_type': employee_type,
                'department': department,
                'position': position,
                'workplace': workplace,
                'probation_start': probation_start,
                'official_start_date': official_start_date,
                'work_status': work_status,
                'manager_user': manager_user,
                'leader_user': leader_user,
            })

            # Lưu thông tin hợp đồng
            save_contract_info_from_data(user, {
                'contract_number': contract_number,
                'contract_type': contract_type,
                'contract_signed_date': contract_signed_date,
                'contract_start_date': contract_start_date,
                'contract_end_date': contract_end_date,
                'contract_annual_leave_days': contract_annual_leave_days,
                'contract_standard_shift': contract_standard_shift,
                'contract_attachment_reference': contract_attachment_reference,
            })

            display_name = full_name or employee_id
            messages.success(
                request,
                f'✅ Đã tạo hồ sơ và tài khoản cho "{display_name}"! '
                f'Username: {username} | Mật khẩu: {password}'
            )
        else:
            # Hồ sơ (UserProfile/work info/HĐ) đều gắn FK tới một User → không thể lưu
            # nếu không tạo tài khoản. Báo rõ thay vì giả thành công làm mất dữ liệu.
            messages.error(
                request,
                'Vui lòng bật "Tạo tài khoản đăng nhập" để lưu hồ sơ — '
                'hồ sơ nhân viên phải gắn với một tài khoản.',
            )
            return render(
                request,
                'employee_profiles/hr_create_profile.html',
                build_hr_create_profile_context(request.POST),
            )

        return redirect('hr_create_profile')

    return render(
        request,
        'employee_profiles/hr_create_profile.html',
        build_hr_create_profile_context(),
    )


@login_required
@user_passes_test(can_manage_work_info)
def edit_work_info_view(request, user_id):
    """
    HR/Admin chỉnh toàn bộ hồ sơ nhân viên (bao gồm vai trò).
    Template: employee_profiles/edit_work_info.html
    """
    if is_admin_user(request.user):
        messages.error(request, 'Tài khoản Admin không có quyền chỉnh sửa hồ sơ nhân sự.')
        return redirect('user_list')

    target_user = get_object_or_404(User, pk=user_id)
    profile = ensure_profile(target_user)
    work_info = ensure_work_info(target_user)
    ensure_contract_info(target_user)
    personal_info = ensure_personal_info(target_user)
    emergency_contact = ensure_emergency_contact(target_user)
    education_info = ensure_education_info(target_user)

    manager_queryset = get_manager_user_queryset()
    leader_queryset = get_leader_user_queryset()
    editor_is_admin = is_admin_user(request.user)

    if request.method == 'POST':
        form = EmployeeProfileForm(
            request.POST,
            manager_queryset=manager_queryset,
            leader_queryset=leader_queryset,
            current_user=target_user,
            is_admin_editor=editor_is_admin,
        )
        if form.is_valid():
            # Lưu thông tin cá nhân vào UserProfile
            email = form.cleaned_data['email']
            target_user.email = email
            target_user.save(update_fields=['email'])
            profile.full_name = form.cleaned_data['full_name']
            profile.employee_id = form.cleaned_data['employee_id']

            profile.save()

            # Lưu thông tin công việc vào EmployeeWorkInfo
            save_work_info_from_data(target_user, form.cleaned_data)

            # Lưu thông tin bổ sung (Cá nhân, Liên hệ, Học vấn)
            save_personal_info_from_data(target_user, form.cleaned_data)
            save_emergency_contact_from_data(target_user, form.cleaned_data)
            save_education_info_from_data(target_user, form.cleaned_data)
            messages.success(request, f'Đã cập nhật hồ sơ nhân sự cho "{target_user.username}".')
            return redirect('hr_view_profile', user_id=target_user.pk)
    else:
        form = EmployeeProfileForm(
            initial={
                'full_name': profile.full_name,
                'email': target_user.email,
                'phone_number': personal_info.phone_number,
                'date_of_birth': personal_info.date_of_birth,
                'employee_id': profile.employee_id,
                'department': work_info.department,
                'employee_type': work_info.employee_type,
                'position': work_info.position,
                'workplace': work_info.workplace,
                'probation_start': work_info.probation_start,
                'official_start_date': work_info.official_start_date,
                'work_status': work_info.work_status,
                'manager_user': work_info.manager_user,
                'leader_user': work_info.leader_user,
                # Thông tin cá nhân mở rộng
                'gender': personal_info.gender,
                'marital_status': personal_info.marital_status,
                'nationality': personal_info.nationality,
                'id_card_number': personal_info.id_card_number,
                'id_card_issue_place': personal_info.id_card_issue_place,
                'id_card_issue_date': personal_info.id_card_issue_date,
                'permanent_address': personal_info.permanent_address,
                'temporary_address': personal_info.temporary_address,
                # Người liên hệ khẩn cấp
                'contact_name': emergency_contact.contact_name,
                'contact_phone': emergency_contact.contact_phone,
                'relation': emergency_contact.relation,
                'contact_address': emergency_contact.contact_address,
                # Học vấn & Năng lực
                'education_level': education_info.education_level,
                'degree': education_info.degree,
                'major': education_info.major,
                'certificates': education_info.certificates,
                'foreign_languages': education_info.foreign_languages,
                'professional_skills': education_info.professional_skills,
            },
            manager_queryset=manager_queryset,
            leader_queryset=leader_queryset,
            current_user=target_user,
            is_admin_editor=editor_is_admin,
        )

    return render(request, 'employee_profiles/edit_work_info.html', {
        'form': form,
        'target_user': target_user,
        'active_page': 'users',
        'can_manage_system_users': editor_is_admin,
        'major_suggestions': MAJOR_SUGGESTIONS,
    })


@login_required
@user_passes_test(can_manage_work_info)
def hr_assign_role_view(request, user_id):
    """
    Trang phân vai trò HỢP NHẤT cho HR + Admin (UI card picker).
    - HR: chỉ được gán Employee, Leader, Manager, HR (không Admin).
    - Admin: gán tất cả vai trò.
    Sau khi lưu: Admin → user_list (quản lý tài khoản hệ thống);
    HR → hồ sơ nhân viên.
    Template: employee_profiles/hr_assign_role.html
    """
    target_user = get_object_or_404(User, pk=user_id)
    profile = ensure_profile(target_user)
    editor_is_admin = is_admin_user(request.user)

    # Đích quay về tuỳ người dùng: admin không có trang hồ sơ nhân sự.
    done_redirect = redirect('user_list') if editor_is_admin \
        else redirect('hr_view_profile', user_id=target_user.pk)

    # Lấy danh sách vai trò phù hợp
    if editor_is_admin:
        available_roles = Role.objects.all()
    else:
        available_roles = Role.objects.exclude(name=Role.ADMIN)

    if request.method == 'POST':
        role_id = request.POST.get('role', '').strip()
        if role_id:
            try:
                new_role = Role.objects.get(pk=role_id)
                # Bảo vệ: HR không được gán Admin
                if new_role.name == Role.ADMIN and not editor_is_admin:
                    messages.error(request, 'Bạn không có quyền gán vai trò Admin.')
                    return redirect('hr_assign_role', user_id=target_user.pk)
                profile.role = new_role
                profile.save()
                create_notification(
                    target_user,
                    'Vai trò của bạn đã thay đổi',
                    f'Vai trò của bạn đã được cập nhật thành "{new_role.get_name_display()}".',
                )
                messages.success(
                    request,
                    f'Đã cập nhật vai trò "{new_role.get_name_display()}" cho "{profile.full_name or target_user.username}".'
                )
            except Role.DoesNotExist:
                messages.error(request, 'Vai trò không hợp lệ.')
        else:
            profile.role = None
            profile.save()
            messages.success(request, f'Đã bỏ gán vai trò cho "{profile.full_name or target_user.username}".')
        return done_redirect

    return render(request, 'employee_profiles/hr_assign_role.html', {
        'target_user': target_user,
        'profile': profile,
        'available_roles': available_roles,
        'active_page': 'users',
        'editor_is_admin': editor_is_admin,
    })
