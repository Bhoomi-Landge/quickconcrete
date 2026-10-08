"""Centralized ownership and role authorization helpers."""


class AccessError(Exception):
    def __init__(self, message="Not found.", status_code=404):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def deny_cross_tenant():
    raise AccessError("Not found.", 404)


def require_role(user, role):
    if not user:
        raise AccessError("Not authenticated.", 401)
    if user.role != role:
        raise AccessError("Forbidden.", 403)
