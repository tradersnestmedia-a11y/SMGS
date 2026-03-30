from functools import wraps

from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login

from .models import UserProfile


def ensure_profile(user):
    if not user.is_authenticated:
        return None
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={"role": UserProfile.ROLE_ADMIN if user.is_superuser else UserProfile.ROLE_STUDENT},
    )
    return profile


def get_user_role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return UserProfile.ROLE_ADMIN
    return ensure_profile(user).role


def is_admin(user):
    return get_user_role(user) == UserProfile.ROLE_ADMIN


def is_teacher(user):
    return get_user_role(user) == UserProfile.ROLE_TEACHER


def is_student(user):
    return get_user_role(user) == UserProfile.ROLE_STUDENT


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if get_user_role(request.user) not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
