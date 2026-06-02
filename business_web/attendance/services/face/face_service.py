"""Register employee face on the remote service; keep a minimal local row.

Remote-first: nếu remote /register từ chối ảnh, không ghi row local.
EmployeeFace chỉ giữ slot_id (đánh dấu đã enroll). Ảnh KHÔNG lưu local —
nhận diện chạy remote (FAISS).
"""
from attendance.models import EmployeeFace
from attendance.services.face import face_api_client


def resolve_slot_id(user) -> int:
    """Slot hiện có của user, hoặc 1 nếu chưa enroll."""
    existing = EmployeeFace.objects.filter(user=user).first()
    return existing.slot_id if existing else 1


def apply_face_enrollment(user, raw_bytes) -> EmployeeFace:
    """Đẩy ảnh lên service từ xa rồi upsert row local (chỉ slot_id).

    Điểm DUY NHẤT khiến một khuôn mặt trở thành enrollment có hiệu lực.
    Remote `/register` luôn nhận bytes (filename jpg cố định phía client).
    Raises FaceApiError nếu remote từ chối.
    """
    slot_id = resolve_slot_id(user)
    face_api_client.register_face_remote(
        employee_id=str(user.id),
        image_bytes=raw_bytes,
        slot_id=slot_id,
    )
    face, _ = EmployeeFace.objects.update_or_create(
        user=user,
        defaults={'slot_id': slot_id},
    )
    return face


def delete_employee_face(user) -> bool:
    deleted_count, _ = EmployeeFace.objects.filter(user=user).delete()
    return deleted_count > 0
