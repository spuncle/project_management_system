from functools import wraps
from flask import abort
from flask_login import current_user

def permission_required(permission_name):
    """
    一个检查用户是否拥有特定权限的装饰器。
    管理员(is_admin)拥有所有权限。
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if not getattr(current_user, permission_name, False) and not current_user.is_admin:
                abort(403)  # 403 Forbidden
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """
    一个检查用户是否是管理员的装饰器。
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function