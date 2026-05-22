"""Service lưu và truy xuất ảnh base64 khuôn mặt nhân viên."""
from django.contrib.auth.models import User

from attendance.models import EmployeeFace
from attendance.services.image_service import image_to_base64


def save_employee_face(user, image_file) -> EmployeeFace:
    """
    Chuyển ảnh sang base64 và lưu vào database cho nhân viên.

    Nếu nhân viên đã có ảnh trước đó, sẽ cập nhật ảnh mới (ghi đè).

    Args:
        user: Django User object (nhân viên).
        image_file: File ảnh (Django UploadedFile).

    Returns:
        EmployeeFace: Bản ghi đã lưu/cập nhật.

    Raises:
        ValueError: Nếu không thể chuyển ảnh sang base64.
    """
    base64_str = image_to_base64(image_file)
    content_type = getattr(image_file, 'content_type', 'image/png')

    face, created = EmployeeFace.objects.update_or_create(
        user=user,
        defaults={
            'face_base64': base64_str,
            'content_type': content_type,
        },
    )
    return face


def get_employee_face(user) -> dict | None:
    """
    Lấy ảnh base64 khuôn mặt của nhân viên từ database.

    Args:
        user: Django User object.

    Returns:
        dict với keys 'base64', 'content_type', 'updated_at' nếu tìm thấy.
        None nếu nhân viên chưa có ảnh.
    """
    try:
        face = EmployeeFace.objects.get(user=user)
        return {
            'base64': face.face_base64,
            'content_type': face.content_type,
            'updated_at': face.updated_at,
        }
    except EmployeeFace.DoesNotExist:
        return None


def delete_employee_face(user) -> bool:
    """
    Xóa ảnh khuôn mặt của nhân viên.

    Args:
        user: Django User object.

    Returns:
        True nếu xóa thành công, False nếu không tìm thấy.
    """
    deleted_count, _ = EmployeeFace.objects.filter(user=user).delete()
    return deleted_count > 0
