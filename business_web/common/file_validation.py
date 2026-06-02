"""Validator upload dùng chung cho mọi FileField (định dạng + dung lượng).

Gom logic kiểm tra 5 MB + MIME vốn bị lặp ở từng form (leaves, overtime,
attendance, reports, rewards...). Dùng được cả trong form `clean_*` lẫn view
vì raise ``django.core.exceptions.ValidationError`` (cùng lớp với
``django.forms.ValidationError``).
"""
from django.core.exceptions import ValidationError

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB

# Tài liệu/minh chứng thông thường: PDF + ảnh phổ biến.
DOCUMENT_MIME = {'application/pdf', 'image/jpeg', 'image/png'}
# Minh chứng (đính kèm linh hoạt hơn): thêm gif/webp.
EVIDENCE_MIME = DOCUMENT_MIME | {'image/gif', 'image/webp'}

OVERSIZE_MESSAGE = 'Tệp tối đa 5 MB.'
MIME_MESSAGE = 'Sai định dạng. Chấp nhận: PDF, JPG, PNG.'
REQUIRED_MESSAGE = 'Vui lòng đính kèm tệp.'


def validate_upload(
    f,
    *,
    required=False,
    max_bytes=MAX_UPLOAD_BYTES,
    allowed_mime=DOCUMENT_MIME,
    required_message=REQUIRED_MESSAGE,
    oversize_message=OVERSIZE_MESSAGE,
    mime_message=MIME_MESSAGE,
):
    """Kiểm tra tệp upload. Trả lại ``f`` nếu hợp lệ, raise ValidationError nếu không.

    - ``f`` rỗng + ``required=False`` → trả None (bỏ qua).
    - ``f`` rỗng + ``required=True`` → raise ``required_message``.
    - quá ``max_bytes`` → raise ``oversize_message``.
    - MIME không thuộc ``allowed_mime`` → raise ``mime_message``.
    """
    if not f:
        if required:
            raise ValidationError(required_message)
        return f
    if f.size > max_bytes:
        raise ValidationError(oversize_message)
    content_type = getattr(f, 'content_type', '') or ''
    if content_type not in allowed_mime:
        raise ValidationError(mime_message)
    return f
