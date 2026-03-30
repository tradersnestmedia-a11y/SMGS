from django.urls import path

from . import views

app_name = "students"

urlpatterns = [
    path("", views.student_list_view, name="list"),
    path("add/", views.student_create_view, name="add"),
    path("<int:pk>/", views.student_detail_view, name="detail"),
    path("<int:pk>/edit/", views.student_update_view, name="edit"),
    path("<int:pk>/delete/", views.student_delete_view, name="delete"),
]
