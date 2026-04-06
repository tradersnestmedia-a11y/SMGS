from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("students/", include("students.urls")),
    path("teachers/", include("teachers.urls")),
    path("academics/", include("academics.urls")),
]

# Render uses Django directly behind Gunicorn, so local media files need an explicit route
# even when DEBUG is off.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
