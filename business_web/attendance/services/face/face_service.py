"""Register employee face on the remote service; keep a local preview row.

Remote-first: if the remote /register rejects the image, no local row is
written. The local EmployeeFace row only stores base64 (for UI preview) and
the pinned slot_id. The face vector itself lives on the remote service.
"""
from attendance.models import EmployeeFace
from attendance.services.face import face_api_client
from attendance.services.face.image_service import image_to_base64


def resolve_slot_id(user) -> int:
    """Slot hiện có của user, hoặc 1 nếu chưa enroll."""
    existing = EmployeeFace.objects.filter(user=user).first()
    return existing.slot_id if existing else 1


def apply_face_enrollment(user, raw_bytes, base64_str, content_type) -> EmployeeFace:
    """Đẩy ảnh lên service từ xa rồi upsert row preview local.

    Đây là điểm DUY NHẤT khiến một khuôn mặt trở thành enrollment có hiệu lực.
    Raises FaceApiError nếu remote từ chối (no-face / lỗi).
    """
    slot_id = resolve_slot_id(user)
    face_api_client.register_face_remote(
        employee_id=str(user.id),
        image_bytes=raw_bytes,
        slot_id=slot_id,
    )
    face, _ = EmployeeFace.objects.update_or_create(
        user=user,
        defaults={
            'face_base64': base64_str,
            'content_type': content_type,
            'slot_id': slot_id,
        },
    )
    return face


def save_employee_face(user, image_file) -> EmployeeFace:
    """Enroll trực tiếp (đường tin cậy — VD HR/Admin). Có hiệu lực ngay."""
    image_file.seek(0)
    raw_bytes = image_file.read()
    image_file.seek(0)
    base64_str = image_to_base64(image_file)
    content_type = getattr(image_file, 'content_type', 'image/png')
    return apply_face_enrollment(user, raw_bytes, base64_str, content_type)


def get_employee_face(user) -> dict | None:
    try:
        face = EmployeeFace.objects.get(user=user)
    except EmployeeFace.DoesNotExist:
        return None
    return {
        'base64': face.face_base64,
        'content_type': face.content_type,
        'updated_at': face.updated_at,
    }


def delete_employee_face(user) -> bool:
    deleted_count, _ = EmployeeFace.objects.filter(user=user).delete()
    return deleted_count > 0
