from django.conf import settings

from .permissions import get_user_role


def school_context(request):
    return {
        "school_name": settings.SCHOOL_NAME,
        "current_role": get_user_role(request.user) if request.user.is_authenticated else None,
    }
