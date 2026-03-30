from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.home_redirect, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("profile/", views.account_profile_view, name="profile"),
    path("register/student/", views.student_registration_view, name="student_register"),
    path("register/staff/", views.staff_registration_view, name="staff_register"),
    path("register/success/", views.registration_success_view, name="registration_success"),
    path("registrations/", views.registration_dashboard_view, name="registration_dashboard"),
    path("registrations/students/<int:pk>/", views.student_registration_detail_view, name="student_registration_detail"),
    path("registrations/staff/<int:pk>/", views.staff_registration_detail_view, name="staff_registration_detail"),
]
