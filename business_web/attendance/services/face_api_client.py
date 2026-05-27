"""Pure HTTP client for the FastAPI face recognition service.

Single responsibility: talk to the FastAPI endpoints. No Django models touched.
Reads `FACE_API_URL` and `FACE_API_TIMEOUT_SEC` from settings.
"""
import logging
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger('face.client')


class FaceApiError(Exception):
    """Wraps any failure talking to the face service.

    code is one of: 'unreachable', 'timeout', 'bad_response', 'no_face', 'unknown'.
    """

    def __init__(self, code: str, message: str = ''):
        super().__init__(message or code)
        self.code = code
        self.message = message


def _url(path: str) -> str:
    base = settings.FACE_API_URL.rstrip('/')
    return f'{base}{path}'


def _classify_post_failure(exc: Exception) -> FaceApiError:
    if isinstance(exc, requests.Timeout):
        return FaceApiError('timeout', str(exc))
    if isinstance(exc, requests.ConnectionError):
        return FaceApiError('unreachable', str(exc))
    return FaceApiError('unknown', str(exc))


def health_check() -> bool:
    """Return True iff FastAPI `/health` reports status == 'ok'."""
    try:
        resp = requests.get(_url('/health'),
                            timeout=settings.FACE_API_TIMEOUT_SEC)
    except requests.RequestException as exc:
        logger.warning('face health unreachable: %s', exc)
        return False
    if resp.status_code != 200:
        return False
    try:
        body = resp.json()
    except ValueError:
        return False
    return body.get('status') == 'ok'


def register_face_remote(employee_id: str, image_bytes: bytes,
                         filename: str = 'face.jpg',
                         slot_id: Optional[int] = None) -> dict:
    """POST /register multipart. Returns parsed JSON.

    Raises FaceApiError on transport failure or non-success HTTP status.
    """
    data = {'employee_id': employee_id}
    if slot_id is not None:
        data['slot_id'] = slot_id
    files = {'file': (filename, image_bytes, 'image/jpeg')}
    try:
        resp = requests.post(_url('/register'),
                             data=data, files=files,
                             timeout=settings.FACE_API_TIMEOUT_SEC)
    except requests.RequestException as exc:
        raise _classify_post_failure(exc) from exc

    return _parse_post_response(resp)


def recognize_face_remote(image_bytes: bytes,
                          filename: str = 'probe.jpg') -> dict:
    """POST /recognize multipart. Returns parsed JSON.

    Does NOT raise on `status='fail'` — caller interprets the body.
    Raises FaceApiError only on transport failure or non-2xx HTTP.
    """
    files = {'file': (filename, image_bytes, 'image/jpeg')}
    try:
        resp = requests.post(_url('/recognize'),
                             files=files,
                             timeout=settings.FACE_API_TIMEOUT_SEC)
    except requests.RequestException as exc:
        raise _classify_post_failure(exc) from exc

    return _parse_post_response(resp)


def _parse_post_response(resp) -> dict:
    if resp.status_code == 400:
        text = (resp.text or '').lower()
        if 'no face' in text:
            raise FaceApiError('no_face', resp.text)
        raise FaceApiError('bad_response', resp.text)
    if not (200 <= resp.status_code < 300):
        raise FaceApiError('bad_response', f'HTTP {resp.status_code}: {resp.text}')
    try:
        return resp.json()
    except ValueError as exc:
        raise FaceApiError('bad_response', f'JSON decode failure: {exc}') from exc
