"""POST /attendance/check/ — runs face verification, logs attendance."""
import logging
from datetime import time as _time

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from attendance.models import AttendanceRecord
from attendance.services.attendance_logging_service import (
    decide_next_action,
    get_open_previous_record,
    record_check_in,
    record_check_out,
)
from attendance.services.face_lockout_service import (
    clear_failures, is_locked, register_failure,
)
from attendance.services.face_verification_service import verify_face_for_user

logger = logging.getLogger('face.attendance')

MAX_IMAGE_BYTES = 2 * 1024 * 1024  # 2 MB defensive cap


def _fails_left(user):
    from django.core.cache import cache
    remaining = settings.FACE_LOCKOUT_MAX_FAILS - (
        cache.get(f'face_lockout:fails:{user.id}') or 0
    )
    return max(remaining, 0)


def _extract_image_bytes(request):
    upload = request.FILES.get('image')
    if not upload:
        return None, JsonResponse(
            {'error': 'no_image'}, status=400,
        )
    if upload.size > MAX_IMAGE_BYTES:
        return None, JsonResponse(
            {'error': 'image_too_large', 'max_bytes': MAX_IMAGE_BYTES},
            status=400,
        )
    return upload.read(), None


def _previous_open_payload(user):
    prev = get_open_previous_record(user)
    if prev is None:
        return None
    return {'id': prev.id, 'date': prev.record_date.isoformat()}


@login_required
@require_POST
def face_check_view(request):
    # 1. Lockout gate.
    locked, retry_after = is_locked(request.user)
    if locked:
        return JsonResponse(
            {'locked': True, 'retry_after': retry_after}, status=423,
        )

    # 2. Image extraction.
    image_bytes, err = _extract_image_bytes(request)
    if err is not None:
        return err

    # 3. Verify.
    result = verify_face_for_user(request.user, image_bytes)
    if not result.success:
        if result.reason == 'wrong_person':
            register_failure(request.user)
            return JsonResponse(
                {'error': 'wrong_person', 'fails_left': _fails_left(request.user)},
                status=403,
            )
        if result.reason == 'no_match':
            return JsonResponse({'error': 'no_match'}, status=401)
        if result.reason == 'no_face':
            return JsonResponse({'error': 'no_face_detected'}, status=400)
        # service_down
        return JsonResponse(
            {'error': 'face_service_unavailable'}, status=503,
        )

    # 4. Success path — race-safe.
    with transaction.atomic():
        record = (AttendanceRecord.objects
                  .select_for_update()
                  .get_or_create(user=request.user,
                                 record_date=timezone.localdate()))[0]
        action = decide_next_action(record)
        if action == 'check_in':
            record_check_in(request.user)
        elif action == 'check_out':
            record_check_out(request.user)
        # 'done' → no-op

    clear_failures(request.user)

    record.refresh_from_db()
    payload = {
        'success': True,
        'action': action,
        'confidence': result.confidence,
    }
    if action == 'check_in':
        payload['time'] = record.check_in_time.strftime('%H:%M')
        payload['status'] = record.status
    elif action == 'check_out':
        payload['time'] = record.check_out_time.strftime('%H:%M')

    prev = _previous_open_payload(request.user)
    if prev is not None:
        payload['previous_open_record'] = prev

    return JsonResponse(payload, status=200)
