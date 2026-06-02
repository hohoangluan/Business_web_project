"""Public service exports for the attendance app.

Re-exports submodules so existing shallow imports keep working, e.g.
``from attendance.services import face_api_client``.
"""
from attendance.services.face import (
    face_api_client,
    face_lockout_service,
    face_service,
    face_verification_service,
)
from attendance.services.record import attendance_logging_service

__all__ = [
    "face_api_client",
    "face_lockout_service",
    "face_service",
    "face_verification_service",
    "attendance_logging_service",
]
