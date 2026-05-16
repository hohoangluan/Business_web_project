"""Custom permission helper services."""


def has_custom_permission(user, codename):
    """Return whether a user has the given custom permission codename."""

    if not user.is_authenticated:
        return False
    profile = getattr(user, "profile", None)
    if not profile:
        return False
    return profile.has_custom_permission(codename)
