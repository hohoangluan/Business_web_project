"""Forgot password helper services."""


def mask_email(email):
    """Mask the local part of an email address for recovery UI."""

    if not email or "@" not in email:
        return email or ""

    local_part, domain = email.split("@", 1)
    if len(local_part) <= 2:
        masked_local = local_part[:1] + "*"
    else:
        masked_local = local_part[0] + ("*" * (len(local_part) - 2)) + local_part[-1]
    return f"{masked_local}@{domain}"
