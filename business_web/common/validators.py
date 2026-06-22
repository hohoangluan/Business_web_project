import re

from django.core.exceptions import ValidationError

_PHONE_RE = re.compile(r'^0\d{9}$')


def validate_phone_number(value):
    value = (value or '').strip()
    if not value:
        return ''
    if not _PHONE_RE.match(value):
        raise ValidationError('Số điện thoại phải gồm 10 chữ số và bắt đầu bằng 0.')
    return value
