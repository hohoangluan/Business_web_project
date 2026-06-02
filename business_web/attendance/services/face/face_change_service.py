"""Workflow duyệt cập nhật khuôn mặt (chống gian lận buddy-punching).

Self-service đổi mặt → tạo FaceChangeRequest `pending`, KHÔNG đổi enrollment
đang dùng để nhận diện. HR duyệt mới đẩy lên service từ xa và cập nhật
EmployeeFace. Đường tin cậy (HR/Admin upload) thì áp dụng ngay.
"""
import hashlib

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from accounts.services.permission.role_service import is_admin_user, is_hr_user
from attendance.models import FaceChangeRequest
from attendance.services.face import face_api_client, face_service


def _is_trusted(actor) -> bool:
    """HR/Admin được enroll trực tiếp, không cần qua bước duyệt."""
    return is_hr_user(actor) or is_admin_user(actor)


def submit_face_change(owner, submitted_by, image_file, ip_address=None):
    """Nộp cập nhật khuôn mặt. Trả (outcome, obj)."""
    image_file.seek(0)
    raw_bytes = image_file.read()
    image_file.seek(0)
    sha = hashlib.sha256(raw_bytes).hexdigest()

    has_face = hasattr(owner, 'employee_face')
    # Đường tin cậy (HR/Admin) HOẶC lần đầu → enroll ngay, KHÔNG lưu ảnh.
    if _is_trusted(submitted_by) or not has_face:
        face = face_service.apply_face_enrollment(owner, raw_bytes)
        note = ('Tự động duyệt (người thực hiện là HR/Admin).'
                if _is_trusted(submitted_by) else 'Tự động duyệt (Lần đầu đăng ký).')
        FaceChangeRequest.objects.create(
            user=owner, submitted_by=submitted_by,
            image_sha256=sha, ip_address=ip_address,
            status=FaceChangeRequest.APPROVED,
            reviewed_by=submitted_by, reviewed_at=timezone.now(),
            hr_note=note,
        )
        return 'applied', face

    # Self-service: chờ HR duyệt — lưu ảnh để HR xem (Cloudinary).
    with transaction.atomic():
        FaceChangeRequest.objects.filter(
            user=owner, status=FaceChangeRequest.PENDING,
        ).delete()
        req = FaceChangeRequest.objects.create(
            user=owner, submitted_by=submitted_by,
            image=ContentFile(raw_bytes, name=f'{owner.id}_{sha[:10]}.jpg'),
            image_sha256=sha, ip_address=ip_address,
            status=FaceChangeRequest.PENDING,
        )
    return 'pending', req


def get_pending_face_changes():
    return (FaceChangeRequest.objects
            .filter(status=FaceChangeRequest.PENDING)
            .select_related('user', 'user__profile', 'submitted_by')
            .order_by('-created_at'))


def get_reviewed_face_changes():
    return (FaceChangeRequest.objects
            .exclude(status=FaceChangeRequest.PENDING)
            .select_related('user', 'submitted_by', 'reviewed_by')
            .order_by('-reviewed_at'))


def approve_face_change(hr_user, req_id, hr_note=''):
    try:
        req = FaceChangeRequest.objects.select_related('user').get(id=req_id)
    except FaceChangeRequest.DoesNotExist:
        return False, 'Không tìm thấy yêu cầu.'
    if req.status != FaceChangeRequest.PENDING:
        return False, 'Yêu cầu đã được xử lý.'
    if not req.image:
        return False, 'Thiếu ảnh để duyệt.'

    raw_bytes = req.image.read()
    try:
        face_service.apply_face_enrollment(req.user, raw_bytes)
    except face_api_client.FaceApiError as exc:
        return False, f'Service nhận diện từ chối ảnh: {exc.message or exc.code}'

    req.status = FaceChangeRequest.APPROVED
    req.reviewed_by = hr_user
    req.reviewed_at = timezone.now()
    req.hr_note = (hr_note or '').strip()
    # Đã enroll remote → ảnh local hết tác dụng → purge (giảm PII/dung lượng).
    req.image.delete(save=False)
    req.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'hr_note', 'image'])
    return True, 'Đã duyệt và cập nhật khuôn mặt.'


def reject_face_change(hr_user, req_id, hr_note=''):
    try:
        req = FaceChangeRequest.objects.get(id=req_id)
    except FaceChangeRequest.DoesNotExist:
        return False, 'Không tìm thấy yêu cầu.'
    if req.status != FaceChangeRequest.PENDING:
        return False, 'Yêu cầu đã được xử lý.'
    # GIỮ req.image làm minh chứng chống gian lận.
    req.status = FaceChangeRequest.REJECTED
    req.reviewed_by = hr_user
    req.reviewed_at = timezone.now()
    req.hr_note = (hr_note or '').strip()
    req.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'hr_note'])
    return True, 'Đã từ chối yêu cầu cập nhật khuôn mặt.'
