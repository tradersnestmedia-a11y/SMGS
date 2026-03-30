from django.urls import path

from . import views

app_name = "teachers"

urlpatterns = [
    path("", views.teacher_list_view, name="list"),
    path("add/", views.teacher_create_view, name="add"),
    path("<int:pk>/", views.teacher_detail_view, name="detail"),
    path("<int:pk>/edit/", views.teacher_update_view, name="edit"),
    path("<int:pk>/delete/", views.teacher_delete_view, name="delete"),
]
