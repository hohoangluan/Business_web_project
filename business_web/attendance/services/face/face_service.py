"""Persist employee face image AND mirror to FastAPI registry.

Remote-first: if FastAPI rejects, no local row is created. The local
EmployeeFace row stores base64 for preview and the pinned slot_id so
re-enrollment always overwrites the same Mongo document.
"""
from django.contrib.auth.models import User

from attendance.models import EmployeeFace
from attendance.services.face import face_api_client
from attendance.services.face.image_service import image_to_base64


def save_employee_face(user, image_file) -> EmployeeFace:
    # 1. Read raw bytes once (without disturbing later base64 conversion).
    image_file.seek(0)
    raw_bytes = image_file.read()
    image_file.seek(0)

    # 2. Base64 for local preview.
    base64_str = image_to_base64(image_file)
    content_type = getattr(image_file, 'content_type', 'image/png')

    # 3. Resolve slot_id (existing or default 1).
    existing = EmployeeFace.objects.filter(user=user).first()
    slot_id = existing.slot_id if existing else 1

    # 4. Local extraction
    result = face_api_client.register_face_remote(
        employee_id=str(user.id),
        image_bytes=raw_bytes,
        filename=getattr(image_file, 'name', 'face.jpg'),
        slot_id=slot_id,
    )
    embedding = result.get('embedding')

    # 5. Local upsert.
    face, _ = EmployeeFace.objects.update_or_create(
        user=user,
        defaults={
            'face_base64': base64_str,
            'content_type': content_type,
            'slot_id': slot_id,
            'embedding': embedding,
        },
    )
    return face


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
