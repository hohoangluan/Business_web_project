"""1:1 face verification orchestration.

The only place that knows the rule: `recognized employee_id == str(user.id)`.
"""
import logging
from dataclasses import dataclass
from typing import Optional

from attendance.services import face_api_client

logger = logging.getLogger('face.verify')


@dataclass
class VerifyResult:
    success: bool
    confidence: Optional[float]
    matched_employee_id: Optional[str]
    reason: str  # 'ok' | 'wrong_person' | 'no_match' | 'no_face' | 'service_down'


def _parse_confidence(raw) -> Optional[float]:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).strip().rstrip('%')
    try:
        return float(s)
    except ValueError:
        return None


def verify_face_for_user(user, image_bytes: bytes) -> VerifyResult:
    try:
        body = face_api_client.recognize_face_remote(image_bytes)
    except face_api_client.FaceApiError as exc:
        if exc.code == 'no_face':
            reason = 'no_face'
        else:
            reason = 'service_down'
        logger.info('verify user=%s reason=%s', user.id, reason)
        return VerifyResult(False, None, None, reason)

    if body.get('status') != 'success':
        logger.info('verify user=%s reason=no_match', user.id)
        return VerifyResult(False, None, None, 'no_match')

    matched = str(body.get('employee_id'))
    confidence = _parse_confidence(body.get('confidence'))
    if matched != str(user.id):
        logger.info('verify user=%s reason=wrong_person matched=%s',
                    user.id, matched)
        return VerifyResult(False, confidence, matched, 'wrong_person')

    logger.info('verify user=%s reason=ok confidence=%s', user.id, confidence)
    return VerifyResult(True, confidence, matched, 'ok')
