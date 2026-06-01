"""HTTP client for the remote face-recognition API.

Thin wrapper over two endpoints on the hosted service:
  - POST /register   (employee_id, slot_id, file)  -> stores the face
  - POST /recognize  (file)                         -> identifies the face

All embedding extraction, vector storage and matching happen on the remote
service. This module only ships bytes and parses the JSON reply. No local AI
model is loaded.
"""
import logging
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger('face.engine')


class FaceApiError(Exception):
    def __init__(self, code: str, message: str = ''):
        super().__init__(message or code)
        self.code = code
        self.message = message


def _base_url() -> str:
    return settings.FACE_API_BASE_URL


def _timeout() -> int:
    return settings.FACE_API_TIMEOUT_SEC


# Phrases the remote service (DeepFace enforce_detection) returns when no face
# is present in the uploaded image.
_NO_FACE_HINTS = ('face could not be detected', 'no face', 'face detected')


def _looks_like_no_face(detail: str) -> bool:
    low = (detail or '').lower()
    return any(hint in low for hint in _NO_FACE_HINTS)


def _error_detail(response: requests.Response) -> str:
    """Best-effort extraction of the FastAPI error detail string."""
    try:
        body = response.json()
    except ValueError:
        return response.text or ''
    if isinstance(body, dict):
        return str(body.get('detail') or body.get('message') or body)
    return str(body)


def health_check() -> bool:
    """Return True if the remote service answers /health with status ok."""
    try:
        resp = requests.get(f'{_base_url()}/health', timeout=_timeout())
    except requests.RequestException as exc:
        logger.warning('face health_check failed: %s', exc)
        return False
    if resp.status_code != 200:
        return False
    try:
        return resp.json().get('status') == 'ok'
    except ValueError:
        return False


def register_face_remote(employee_id: str, image_bytes: bytes,
                         filename: str = 'face.jpg',
                         slot_id: Optional[int] = None) -> dict:
    """Register a face on the remote service.

    Returns the parsed JSON body on success (``{"status": "success", ...}``).
    Raises FaceApiError on no-face / bad image / service failures.
    """
    data = {'employee_id': str(employee_id)}
    if slot_id is not None:
        data['slot_id'] = int(slot_id)

    # The remote /register only accepts .jpg/.jpeg/.png filenames.
    files = {'file': ('face.jpg', image_bytes, 'image/jpeg')}

    try:
        resp = requests.post(
            f'{_base_url()}/register',
            data=data, files=files, timeout=_timeout(),
        )
    except requests.RequestException as exc:
        logger.error('face register transport error: %s', exc)
        raise FaceApiError('service_down', f'Face service unreachable: {exc}')

    if resp.status_code == 200:
        return resp.json()

    detail = _error_detail(resp)
    if resp.status_code == 400 and _looks_like_no_face(detail):
        raise FaceApiError('no_face', 'No face detected in image')
    logger.error('face register failed status=%s detail=%s', resp.status_code, detail)
    raise FaceApiError('bad_response', detail or f'HTTP {resp.status_code}')


def recognize_face_remote(image_bytes: bytes,
                          filename: str = 'probe.jpg') -> dict:
    """Identify a face on the remote service.

    Returns the parsed JSON body (``status`` is ``success`` or ``fail``).
    Raises FaceApiError('no_face') when no face is detected, and
    FaceApiError('service_down') / ('bad_response') on transport/HTTP errors.
    """
    files = {'file': ('probe.jpg', image_bytes, 'image/jpeg')}

    try:
        resp = requests.post(
            f'{_base_url()}/recognize',
            files=files, timeout=_timeout(),
        )
    except requests.RequestException as exc:
        logger.error('face recognize transport error: %s', exc)
        raise FaceApiError('service_down', f'Face service unreachable: {exc}')

    if resp.status_code == 200:
        # Either {"status":"success",...} or {"status":"fail","message":...}
        return resp.json()

    detail = _error_detail(resp)
    if resp.status_code == 400 and _looks_like_no_face(detail):
        raise FaceApiError('no_face', 'No face detected in image')
    logger.error('face recognize failed status=%s detail=%s', resp.status_code, detail)
    raise FaceApiError('bad_response', detail or f'HTTP {resp.status_code}')
