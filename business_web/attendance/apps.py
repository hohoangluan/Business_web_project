import logging

from django.apps import AppConfig

logger = logging.getLogger('face.client')


class AttendanceConfig(AppConfig):
    """
    App chấm công.
    Quản lý lịch sử điểm danh, check-in/check-out của nhân viên.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendance'
    verbose_name = 'Chấm công'

    def ready(self):
        # Best-effort warm-up: pay the first HTTP round-trip to the face
        # service before any user click. Failures are logged and ignored
        # because developers may run Django without the face service.
        from attendance.services import face_api_client  # noqa: WPS433
        try:
            face_api_client.health_check()
        except Exception as exc:  # noqa: BLE001 — intentionally broad
            logger.warning('face_api_client warm-up failed: %s', exc)
