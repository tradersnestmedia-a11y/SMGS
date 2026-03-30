# Sim Tech Academy Complete Project Code

This file bundles the main project source into one beginner-friendly reference document.

## manage.py

```python
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'simtech_academy.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

```

## simtech_academy/settings.py

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-sim-tech-academy-demo-key"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "students",
    "teachers",
    "academics",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "simtech_academy.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "accounts.context_processors.school_context",
            ],
        },
    }
]

WSGI_APPLICATION = "simtech_academy.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Lusaka"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"

SCHOOL_NAME = "Sim Tech Academy"

EMAIL_HOST_USER = "tradersnestmedia@gmail.com"
EMAIL_HOST_PASSWORD = os.getenv("SIMTECH_EMAIL_PASSWORD", "")
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
SERVER_EMAIL = EMAIL_HOST_USER
EMAIL_BACKEND = (
    "django.core.mail.backends.smtp.EmailBackend"
    if EMAIL_HOST_PASSWORD
    else "django.core.mail.backends.console.EmailBackend"
)

SIMTECH_SMS_BACKEND = os.getenv("SIMTECH_SMS_BACKEND", "console")
SIMTECH_SMS_ALWAYS_SEND = os.getenv("SIMTECH_SMS_ALWAYS_SEND", "true").lower() in {"1", "true", "yes", "on"}

```

## simtech_academy/urls.py

```python
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

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

```

## accounts/apps.py

```python
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        import accounts.signals  # noqa: F401

```

## accounts/models.py

```python
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


def generate_sequential_identifier(prefix, model_class, field_name):
    year = timezone.now().year
    base = f"{prefix}-{year}-"
    latest_identifier = (
        model_class.objects.filter(**{f"{field_name}__startswith": base})
        .order_by(f"-{field_name}")
        .values_list(field_name, flat=True)
        .first()
    )
    next_number = int(latest_identifier.split("-")[-1]) + 1 if latest_identifier else 1
    return f"{prefix}-{year}-{next_number:04d}"


class UserProfile(models.Model):
    ROLE_ADMIN = "admin"
    ROLE_TEACHER = "teacher"
    ROLE_STUDENT = "student"

    ROLE_CHOICES = (
        (ROLE_ADMIN, "Admin"),
        (ROLE_TEACHER, "Teacher"),
        (ROLE_STUDENT, "Student"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    phone = models.CharField(max_length=20, blank=True)
    photo = models.FileField(upload_to="profile_photos/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


class RegistrationBase(models.Model):
    STATUS_PENDING = "pending_admin"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending Admin Approval"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    )

    full_name = models.CharField(max_length=150)
    nationality = models.CharField(max_length=100)
    zambian_phone = models.CharField(max_length=20)
    personal_email = models.EmailField()
    profile_photo = models.FileField(upload_to="registration_photos/", blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    review_reason = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_%(class)s_records",
    )
    approved_user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_approved_account",
    )
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    notification_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class StudentRegistration(RegistrationBase):
    GRADE_CHOICES = tuple((f"Grade {grade}", f"Grade {grade}") for grade in range(1, 13))

    student_id = models.CharField(max_length=20, unique=True, editable=False)
    date_of_birth = models.DateField()
    guardian_name = models.CharField(max_length=150)
    guardian_relationship = models.CharField(max_length=100)
    guardian_phone = models.CharField(max_length=20)
    guardian_email = models.EmailField()
    previous_school_attended = models.CharField(max_length=200)
    last_grade_completed = models.CharField(max_length=50)
    year_of_completion = models.PositiveIntegerField()
    target_grade = models.CharField(max_length=20, choices=GRADE_CHOICES)
    last_report_card = models.FileField(upload_to="student_documents/report_cards/", blank=True, null=True)
    birth_certificate = models.FileField(upload_to="student_documents/birth_certificates/", blank=True, null=True)
    transfer_letter = models.FileField(upload_to="student_documents/transfer_letters/", blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.student_id:
            self.student_id = generate_sequential_identifier("STU", StudentRegistration, "student_id")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student_id} - {self.full_name}"


class StaffRegistration(RegistrationBase):
    employee_id = models.CharField(max_length=20, unique=True, editable=False)
    qualifications = models.TextField()
    department = models.CharField(max_length=150)
    position_applying_for = models.CharField(max_length=150)

    def save(self, *args, **kwargs):
        if not self.employee_id:
            self.employee_id = generate_sequential_identifier("EMP", StaffRegistration, "employee_id")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee_id} - {self.full_name}"


class NotificationLog(models.Model):
    CHANNEL_EMAIL = "email"
    CHANNEL_SMS = "sms"

    STATUS_SENT = "sent"
    STATUS_FAILED = "failed"
    STATUS_SKIPPED = "skipped"

    CHANNEL_CHOICES = (
        (CHANNEL_EMAIL, "Email"),
        (CHANNEL_SMS, "SMS"),
    )

    STATUS_CHOICES = (
        (STATUS_SENT, "Sent"),
        (STATUS_FAILED, "Failed"),
        (STATUS_SKIPPED, "Skipped"),
    )

    student_registration = models.ForeignKey(
        StudentRegistration,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notification_logs",
    )
    staff_registration = models.ForeignKey(
        StaffRegistration,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notification_logs",
    )
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    recipient = models.CharField(max_length=150)
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    response_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_channel_display()} to {self.recipient} - {self.get_status_display()}"

```

## accounts/forms.py

```python
from datetime import date

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .form_utils import style_form_fields


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "Username",
                "autofocus": True,
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "Password",
            }
        )
    )


class StudentRegistrationPersonalForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    nationality = forms.CharField(max_length=100, initial="Zambian")
    zambian_phone = forms.CharField(max_length=20, help_text="Use a valid Zambian phone number.")
    personal_email = forms.EmailField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)


class StudentRegistrationGuardianForm(forms.Form):
    guardian_name = forms.CharField(max_length=150)
    guardian_relationship = forms.CharField(max_length=100)
    guardian_phone = forms.CharField(max_length=20)
    guardian_email = forms.EmailField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)


class StudentRegistrationAcademicForm(forms.Form):
    previous_school_attended = forms.CharField(max_length=200)
    last_grade_completed = forms.CharField(max_length=50)
    year_of_completion = forms.IntegerField(min_value=2000, max_value=date.today().year)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)


class StudentRegistrationTargetForm(forms.Form):
    target_grade = forms.ChoiceField(choices=tuple((f"Grade {grade}", f"Grade {grade}") for grade in range(1, 13)))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)


class StudentRegistrationDocumentsForm(forms.Form):
    profile_photo = forms.FileField(
        required=True,
        widget=forms.ClearableFileInput(attrs={"accept": "image/*"}),
        help_text="Upload a profile picture for the student profile.",
    )
    last_report_card = forms.FileField(required=True)
    birth_certificate = forms.FileField(required=True)
    transfer_letter = forms.FileField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)


class StaffRegistrationPersonalForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    nationality = forms.CharField(max_length=100, initial="Zambian")
    zambian_phone = forms.CharField(max_length=20, help_text="Use a valid Zambian phone number.")
    personal_email = forms.EmailField()
    qualifications = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)


class StaffRegistrationEmploymentForm(forms.Form):
    department = forms.CharField(max_length=150)
    position_applying_for = forms.CharField(max_length=150)
    profile_photo = forms.FileField(
        required=True,
        widget=forms.ClearableFileInput(attrs={"accept": "image/*"}),
        help_text="Upload a profile picture for the staff profile.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)


class RegistrationDecisionForm(forms.Form):
    review_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Optional reason or approval note"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)

```

## accounts/views.py

```python
from datetime import date

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from academics.models import AttendanceRecord, Grade, SchoolClass, Subject, TeachingAssignment
from students.models import Student
from teachers.models import Teacher

from .forms import (
    LoginForm,
    RegistrationDecisionForm,
    StaffRegistrationEmploymentForm,
    StaffRegistrationPersonalForm,
    StudentRegistrationAcademicForm,
    StudentRegistrationDocumentsForm,
    StudentRegistrationGuardianForm,
    StudentRegistrationPersonalForm,
    StudentRegistrationTargetForm,
)
from .models import StaffRegistration, StudentRegistration, UserProfile
from .permissions import get_user_role, role_required
from .services import approve_staff_registration, approve_student_registration, reject_registration

STUDENT_REGISTRATION_STEPS = [
    ("personal", "Personal Info", StudentRegistrationPersonalForm),
    ("guardian", "Guardian Info", StudentRegistrationGuardianForm),
    ("academic", "Academic History", StudentRegistrationAcademicForm),
    ("target", "Target Enrollment", StudentRegistrationTargetForm),
    ("documents", "Documents", StudentRegistrationDocumentsForm),
]

STAFF_REGISTRATION_STEPS = [
    ("personal", "Personal Info", StaffRegistrationPersonalForm),
    ("employment", "Employment Details", StaffRegistrationEmploymentForm),
]

STUDENT_SESSION_KEY = "student_registration_wizard"
STAFF_SESSION_KEY = "staff_registration_wizard"
REGISTRATION_NOTICE_KEY = "latest_registration_notice"


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    return redirect("accounts:login")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}.")
            return redirect("accounts:dashboard")
        messages.error(request, "Invalid username or password.")

    return render(request, "accounts/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("accounts:login")


def get_step_map(step_config):
    return {key: {"title": title, "form_class": form_class} for key, title, form_class in step_config}


def build_step_items(step_config, current_step, session_data):
    items = []
    for index, (key, title, _) in enumerate(step_config, start=1):
        items.append(
            {
                "key": key,
                "title": title,
                "number": index,
                "is_active": key == current_step,
                "is_complete": key in session_data,
            }
        )
    return items


def get_previous_step(step_config, current_step):
    keys = [key for key, _, _ in step_config]
    index = keys.index(current_step)
    return keys[index - 1] if index > 0 else keys[0]


def get_next_step(step_config, current_step):
    keys = [key for key, _, _ in step_config]
    index = keys.index(current_step)
    return keys[index + 1] if index < len(keys) - 1 else None


def get_first_incomplete_step(step_config, session_data):
    for key, _, _ in step_config:
        if key not in session_data:
            return key
    return step_config[0][0]


def serialize_step_data(cleaned_data):
    serialized = {}
    for key, value in cleaned_data.items():
        if isinstance(value, date):
            serialized[key] = value.isoformat()
        else:
            serialized[key] = value
    return serialized


def hydrate_student_session_data(session_data):
    merged = {}
    for step_values in session_data.values():
        merged.update(step_values)
    if "date_of_birth" in merged and isinstance(merged["date_of_birth"], str):
        merged["date_of_birth"] = date.fromisoformat(merged["date_of_birth"])
    return merged


def hydrate_staff_session_data(session_data):
    merged = {}
    for step_values in session_data.values():
        merged.update(step_values)
    return merged


def student_registration_view(request):
    session_data = request.session.get(STUDENT_SESSION_KEY, {})
    step_map = get_step_map(STUDENT_REGISTRATION_STEPS)
    current_step = request.GET.get("step", STUDENT_REGISTRATION_STEPS[0][0])
    if current_step not in step_map:
        current_step = STUDENT_REGISTRATION_STEPS[0][0]

    required_step = get_first_incomplete_step(STUDENT_REGISTRATION_STEPS, session_data)
    if current_step != STUDENT_REGISTRATION_STEPS[0][0]:
        ordered_keys = [key for key, _, _ in STUDENT_REGISTRATION_STEPS]
        if ordered_keys.index(current_step) > ordered_keys.index(required_step):
            return redirect(f"{reverse('accounts:student_register')}?step={required_step}")

    form_class = step_map[current_step]["form_class"]

    if request.method == "POST":
        current_step = request.POST.get("current_step", current_step)
        action = request.POST.get("action", "next")
        form_class = step_map[current_step]["form_class"]
        form = form_class(request.POST, request.FILES or None)

        if action == "back":
            previous_step = get_previous_step(STUDENT_REGISTRATION_STEPS, current_step)
            return redirect(f"{reverse('accounts:student_register')}?step={previous_step}")

        if form.is_valid():
            if current_step == STUDENT_REGISTRATION_STEPS[-1][0]:
                registration_data = hydrate_student_session_data(session_data)
                registration_data.update(form.cleaned_data)
                registration = StudentRegistration.objects.create(**registration_data)
                request.session.pop(STUDENT_SESSION_KEY, None)
                request.session[REGISTRATION_NOTICE_KEY] = {
                    "type": "Student",
                    "identifier": registration.student_id,
                    "status": "PENDING_ADMIN",
                }
                return redirect("accounts:registration_success")

            session_data[current_step] = serialize_step_data(form.cleaned_data)
            request.session[STUDENT_SESSION_KEY] = session_data
            next_step = get_next_step(STUDENT_REGISTRATION_STEPS, current_step)
            return redirect(f"{reverse('accounts:student_register')}?step={next_step}")
    else:
        form = form_class(initial=session_data.get(current_step, {}))

    return render(
        request,
        "accounts/student_registration.html",
        {
            "form": form,
            "step_items": build_step_items(STUDENT_REGISTRATION_STEPS, current_step, session_data),
            "current_step": current_step,
            "current_title": step_map[current_step]["title"],
            "is_final_step": current_step == STUDENT_REGISTRATION_STEPS[-1][0],
            "back_step": get_previous_step(STUDENT_REGISTRATION_STEPS, current_step),
        },
    )


def staff_registration_view(request):
    session_data = request.session.get(STAFF_SESSION_KEY, {})
    step_map = get_step_map(STAFF_REGISTRATION_STEPS)
    current_step = request.GET.get("step", STAFF_REGISTRATION_STEPS[0][0])
    if current_step not in step_map:
        current_step = STAFF_REGISTRATION_STEPS[0][0]

    required_step = get_first_incomplete_step(STAFF_REGISTRATION_STEPS, session_data)
    if current_step != STAFF_REGISTRATION_STEPS[0][0]:
        ordered_keys = [key for key, _, _ in STAFF_REGISTRATION_STEPS]
        if ordered_keys.index(current_step) > ordered_keys.index(required_step):
            return redirect(f"{reverse('accounts:staff_register')}?step={required_step}")

    form_class = step_map[current_step]["form_class"]

    if request.method == "POST":
        current_step = request.POST.get("current_step", current_step)
        action = request.POST.get("action", "next")
        form_class = step_map[current_step]["form_class"]
        form = form_class(request.POST, request.FILES or None)

        if action == "back":
            previous_step = get_previous_step(STAFF_REGISTRATION_STEPS, current_step)
            return redirect(f"{reverse('accounts:staff_register')}?step={previous_step}")

        if form.is_valid():
            if current_step == STAFF_REGISTRATION_STEPS[-1][0]:
                registration_data = hydrate_staff_session_data(session_data)
                registration_data.update(form.cleaned_data)
                registration = StaffRegistration.objects.create(**registration_data)
                request.session.pop(STAFF_SESSION_KEY, None)
                request.session[REGISTRATION_NOTICE_KEY] = {
                    "type": "Staff",
                    "identifier": registration.employee_id,
                    "status": "PENDING_ADMIN",
                }
                return redirect("accounts:registration_success")

            session_data[current_step] = serialize_step_data(form.cleaned_data)
            request.session[STAFF_SESSION_KEY] = session_data
            next_step = get_next_step(STAFF_REGISTRATION_STEPS, current_step)
            return redirect(f"{reverse('accounts:staff_register')}?step={next_step}")
    else:
        form = form_class(initial=session_data.get(current_step, {}))

    return render(
        request,
        "accounts/staff_registration.html",
        {
            "form": form,
            "step_items": build_step_items(STAFF_REGISTRATION_STEPS, current_step, session_data),
            "current_step": current_step,
            "current_title": step_map[current_step]["title"],
            "is_final_step": current_step == STAFF_REGISTRATION_STEPS[-1][0],
            "back_step": get_previous_step(STAFF_REGISTRATION_STEPS, current_step),
        },
    )


def registration_success_view(request):
    notice = request.session.pop(REGISTRATION_NOTICE_KEY, None)
    return render(request, "accounts/registration_success.html", {"notice": notice})


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def registration_dashboard_view(request):
    pending_students = StudentRegistration.objects.filter(status=StudentRegistration.STATUS_PENDING)
    pending_staff = StaffRegistration.objects.filter(status=StaffRegistration.STATUS_PENDING)
    recent_students = StudentRegistration.objects.exclude(status=StudentRegistration.STATUS_PENDING)[:8]
    recent_staff = StaffRegistration.objects.exclude(status=StaffRegistration.STATUS_PENDING)[:8]
    return render(
        request,
        "accounts/registration_dashboard.html",
        {
            "pending_students": pending_students,
            "pending_staff": pending_staff,
            "recent_students": recent_students,
            "recent_staff": recent_staff,
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def student_registration_detail_view(request, pk):
    registration = get_object_or_404(StudentRegistration, pk=pk)
    review_form = RegistrationDecisionForm(request.POST or None)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "approve":
            try:
                approve_student_registration(
                    registration,
                    request.user,
                    request.build_absolute_uri(reverse("accounts:login")),
                )
                messages.success(request, f"Student registration {registration.student_id} approved successfully.")
                return redirect("accounts:student_registration_detail", pk=registration.pk)
            except ValueError as exc:
                messages.error(request, str(exc))
        elif action == "reject" and review_form.is_valid():
            try:
                reject_registration(registration, request.user, review_form.cleaned_data["review_reason"])
                messages.warning(request, f"Student registration {registration.student_id} was rejected.")
                return redirect("accounts:student_registration_detail", pk=registration.pk)
            except ValueError as exc:
                messages.error(request, str(exc))

    return render(
        request,
        "accounts/student_registration_detail.html",
        {
            "registration": registration,
            "review_form": review_form,
            "notification_logs": registration.notification_logs.all(),
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def staff_registration_detail_view(request, pk):
    registration = get_object_or_404(StaffRegistration, pk=pk)
    review_form = RegistrationDecisionForm(request.POST or None)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "approve":
            try:
                approve_staff_registration(
                    registration,
                    request.user,
                    request.build_absolute_uri(reverse("accounts:login")),
                )
                messages.success(request, f"Staff registration {registration.employee_id} approved successfully.")
                return redirect("accounts:staff_registration_detail", pk=registration.pk)
            except ValueError as exc:
                messages.error(request, str(exc))
        elif action == "reject" and review_form.is_valid():
            try:
                reject_registration(registration, request.user, review_form.cleaned_data["review_reason"])
                messages.warning(request, f"Staff registration {registration.employee_id} was rejected.")
                return redirect("accounts:staff_registration_detail", pk=registration.pk)
            except ValueError as exc:
                messages.error(request, str(exc))

    return render(
        request,
        "accounts/staff_registration_detail.html",
        {
            "registration": registration,
            "review_form": review_form,
            "notification_logs": registration.notification_logs.all(),
        },
    )


@login_required
def dashboard_view(request):
    role = get_user_role(request.user)
    context = {"role": role}

    if role == UserProfile.ROLE_ADMIN:
        context.update(
            {
                "student_count": Student.objects.count(),
                "teacher_count": Teacher.objects.count(),
                "class_count": SchoolClass.objects.count(),
                "subject_count": Subject.objects.count(),
                "attendance_count": AttendanceRecord.objects.count(),
                "grade_count": Grade.objects.count(),
                "pending_student_registrations": StudentRegistration.objects.filter(status=StudentRegistration.STATUS_PENDING).count(),
                "pending_staff_registrations": StaffRegistration.objects.filter(status=StaffRegistration.STATUS_PENDING).count(),
                "recent_grades": Grade.objects.select_related("student", "subject").order_by("-uploaded_at")[:5],
                "recent_attendance": AttendanceRecord.objects.select_related("student", "school_class")
                .order_by("-date", "-id")[:8],
            }
        )
    elif role == UserProfile.ROLE_TEACHER:
        teacher = getattr(request.user, "teacher_profile", None)
        assignments = TeachingAssignment.objects.select_related("school_class", "subject").filter(teacher=teacher)
        context.update(
            {
                "teacher": teacher,
                "assignment_count": assignments.count(),
                "grade_count": Grade.objects.filter(teacher=teacher).count(),
                "attendance_count": AttendanceRecord.objects.filter(marked_by=teacher).count(),
                "assignments": assignments[:6],
            }
        )
    else:
        student = getattr(request.user, "student_profile", None)
        context.update(
            {
                "student": student,
                "grade_count": Grade.objects.filter(student=student).count() if student else 0,
                "attendance_count": AttendanceRecord.objects.filter(student=student).count() if student else 0,
                "results": Grade.objects.select_related("subject").filter(student=student)[:6] if student else [],
            }
        )

    return render(request, "accounts/dashboard.html", context)

```

## accounts/urls.py

```python
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.home_redirect, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("register/student/", views.student_registration_view, name="student_register"),
    path("register/staff/", views.staff_registration_view, name="staff_register"),
    path("register/success/", views.registration_success_view, name="registration_success"),
    path("registrations/", views.registration_dashboard_view, name="registration_dashboard"),
    path("registrations/students/<int:pk>/", views.student_registration_detail_view, name="student_registration_detail"),
    path("registrations/staff/<int:pk>/", views.staff_registration_detail_view, name="staff_registration_detail"),
]

```

## accounts/permissions.py

```python
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

```

## accounts/signals.py

```python
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(
            user=instance,
            role=UserProfile.ROLE_ADMIN if instance.is_superuser else UserProfile.ROLE_STUDENT,
        )
    else:
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={"role": UserProfile.ROLE_ADMIN if instance.is_superuser else UserProfile.ROLE_STUDENT},
        )

```

## accounts/context_processors.py

```python
from django.conf import settings

from .permissions import get_user_role


def school_context(request):
    return {
        "school_name": settings.SCHOOL_NAME,
        "current_role": get_user_role(request.user) if request.user.is_authenticated else None,
    }

```

## accounts/form_utils.py

```python
from django import forms


def style_form_fields(form):
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, (forms.Select, forms.SelectMultiple)):
            base_class = "form-select"
        elif isinstance(widget, forms.CheckboxInput):
            base_class = "form-check-input"
        else:
            base_class = "form-control"

        current_classes = widget.attrs.get("class", "").strip()
        widget.attrs["class"] = f"{current_classes} {base_class}".strip()

```

## accounts/services.py

```python
import logging
import secrets
import string

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from academics.models import SchoolClass
from students.models import Student
from teachers.models import Teacher

from .models import NotificationLog, StaffRegistration, StudentRegistration, UserProfile

logger = logging.getLogger(__name__)


def split_full_name(full_name):
    parts = [part for part in full_name.split() if part.strip()]
    if not parts:
        return "User", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def generate_secure_password(length=12):
    lowercase = secrets.choice(string.ascii_lowercase)
    uppercase = secrets.choice(string.ascii_uppercase)
    digit = secrets.choice(string.digits)
    symbol = secrets.choice("!@#$%^&*")
    remaining_length = max(length - 4, 4)
    pool = string.ascii_letters + string.digits + "!@#$%^&*"
    remaining = "".join(secrets.choice(pool) for _ in range(remaining_length))
    characters = list(lowercase + uppercase + digit + symbol + remaining)
    secrets.SystemRandom().shuffle(characters)
    return "".join(characters)


def build_credential_message(name, username, password, login_url):
    return (
        f"Dear {name}, your registration has been approved by Admin.\n"
        f"Username: {username}\n"
        f"Password: {password}\n"
        f"Login URL: {login_url}"
    )


def log_notification(registration, channel, status, recipient, subject, message, response_message):
    log_kwargs = {
        "channel": channel,
        "status": status,
        "recipient": recipient,
        "subject": subject,
        "message": message,
        "response_message": response_message,
    }
    if isinstance(registration, StudentRegistration):
        log_kwargs["student_registration"] = registration
    else:
        log_kwargs["staff_registration"] = registration
    NotificationLog.objects.create(**log_kwargs)


def send_registration_email(registration, subject, message):
    recipient_email = registration.personal_email
    if not recipient_email:
        log_notification(registration, NotificationLog.CHANNEL_EMAIL, NotificationLog.STATUS_SKIPPED, "", subject, message, "No recipient email supplied.")
        return False, "No recipient email supplied."

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        log_notification(registration, NotificationLog.CHANNEL_EMAIL, NotificationLog.STATUS_SENT, recipient_email, subject, message, "Email sent successfully.")
        return True, "Email sent successfully."
    except Exception as exc:  # pragma: no cover - external delivery failure
        log_notification(registration, NotificationLog.CHANNEL_EMAIL, NotificationLog.STATUS_FAILED, recipient_email, subject, message, str(exc))
        return False, str(exc)


def send_registration_sms(registration, message):
    phone_number = registration.zambian_phone
    if not phone_number:
        log_notification(registration, NotificationLog.CHANNEL_SMS, NotificationLog.STATUS_SKIPPED, "", "", message, "No phone number supplied.")
        return False, "No phone number supplied."

    backend = getattr(settings, "SIMTECH_SMS_BACKEND", "console")
    if backend == "console":
        logger.info("SMS notification to %s: %s", phone_number, message)
        log_notification(
            registration,
            NotificationLog.CHANNEL_SMS,
            NotificationLog.STATUS_SENT,
            phone_number,
            "",
            message,
            "Console SMS backend used. Replace with a real Zambian SMS gateway in production.",
        )
        return True, "Console SMS backend used."

    log_notification(
        registration,
        NotificationLog.CHANNEL_SMS,
        NotificationLog.STATUS_FAILED,
        phone_number,
        "",
        message,
        "No live SMS backend is configured.",
    )
    return False, "No live SMS backend is configured."


def get_matching_class(target_grade):
    return SchoolClass.objects.filter(name__iexact=target_grade).order_by("section").first()


def notify_registration_approval(registration, password, login_url):
    username = registration.student_id if isinstance(registration, StudentRegistration) else registration.employee_id
    message = build_credential_message(registration.full_name, username, password, login_url)
    subject = f"{settings.SCHOOL_NAME}: Registration Approved"
    email_sent, email_response = send_registration_email(registration, subject, message)

    sms_sent = False
    sms_response = "SMS not required."
    if not email_sent or getattr(settings, "SIMTECH_SMS_ALWAYS_SEND", True):
        sms_sent, sms_response = send_registration_sms(registration, message)

    registration.email_sent = email_sent
    registration.sms_sent = sms_sent
    registration.notification_summary = f"Email: {email_response} | SMS: {sms_response}"
    registration.save(update_fields=["email_sent", "sms_sent", "notification_summary", "updated_at"])


@transaction.atomic
def approve_student_registration(registration, admin_user, login_url):
    if registration.status != StudentRegistration.STATUS_PENDING:
        raise ValueError("Only pending student registrations can be approved.")

    first_name, last_name = split_full_name(registration.full_name)
    password = generate_secure_password()
    username = registration.student_id

    user = User.objects.create_user(
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name,
        email=registration.personal_email,
        is_active=True,
    )
    user.profile.role = UserProfile.ROLE_STUDENT
    user.profile.phone = registration.zambian_phone
    if registration.profile_photo:
        user.profile.photo = registration.profile_photo
    user.profile.save()

    Student.objects.create(
        user=user,
        admission_number=username,
        first_name=first_name,
        last_name=last_name or first_name,
        gender="Not Specified",
        date_of_birth=registration.date_of_birth,
        nationality=registration.nationality,
        email=registration.personal_email,
        phone=registration.zambian_phone,
        guardian_name=registration.guardian_name,
        guardian_relationship=registration.guardian_relationship,
        guardian_phone=registration.guardian_phone,
        guardian_email=registration.guardian_email,
        current_class=get_matching_class(registration.target_grade),
        joined_on=timezone.localdate(),
    )

    registration.status = StudentRegistration.STATUS_APPROVED
    registration.reviewed_by = admin_user
    registration.reviewed_at = timezone.now()
    registration.approved_user = user
    registration.review_reason = ""
    registration.save()
    notify_registration_approval(registration, password, login_url)
    return username, password


@transaction.atomic
def approve_staff_registration(registration, admin_user, login_url):
    if registration.status != StaffRegistration.STATUS_PENDING:
        raise ValueError("Only pending staff registrations can be approved.")

    first_name, last_name = split_full_name(registration.full_name)
    password = generate_secure_password()
    username = registration.employee_id

    user = User.objects.create_user(
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name,
        email=registration.personal_email,
        is_active=True,
    )
    user.profile.role = UserProfile.ROLE_TEACHER
    user.profile.phone = registration.zambian_phone
    if registration.profile_photo:
        user.profile.photo = registration.profile_photo
    user.profile.save()

    Teacher.objects.create(
        user=user,
        employee_id=username,
        first_name=first_name,
        last_name=last_name or first_name,
        nationality=registration.nationality,
        email=registration.personal_email,
        phone=registration.zambian_phone,
        specialization=registration.department,
        qualifications=registration.qualifications,
        department=registration.department,
        position=registration.position_applying_for,
        address="",
        hired_on=timezone.localdate(),
    )

    registration.status = StaffRegistration.STATUS_APPROVED
    registration.reviewed_by = admin_user
    registration.reviewed_at = timezone.now()
    registration.approved_user = user
    registration.review_reason = ""
    registration.save()
    notify_registration_approval(registration, password, login_url)
    return username, password


def reject_registration(registration, admin_user, reason=""):
    if registration.status != registration.STATUS_PENDING:
        raise ValueError("Only pending registrations can be rejected.")
    registration.status = registration.STATUS_REJECTED
    registration.review_reason = reason
    registration.reviewed_by = admin_user
    registration.reviewed_at = timezone.now()
    registration.save(update_fields=["status", "review_reason", "reviewed_by", "reviewed_at", "updated_at"])

```

## students/models.py

```python
from django.contrib.auth.models import User
from django.db import models


class Student(models.Model):
    GENDER_CHOICES = (
        ("Male", "Male"),
        ("Female", "Female"),
        ("Not Specified", "Not Specified"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    admission_number = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default="Not Specified")
    date_of_birth = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    guardian_name = models.CharField(max_length=150, blank=True)
    guardian_relationship = models.CharField(max_length=100, blank=True)
    guardian_phone = models.CharField(max_length=20, blank=True)
    guardian_email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    current_class = models.ForeignKey(
        "academics.SchoolClass",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="enrolled_students",
    )
    joined_on = models.DateField()

    class Meta:
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.admission_number} - {self.full_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

```

## students/forms.py

```python
from django import forms
from django.contrib.auth.models import User

from accounts.form_utils import style_form_fields
from accounts.models import UserProfile

from .models import Student


class StudentCreateForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    password1 = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(widget=forms.PasswordInput())
    photo = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"accept": "image/*"}),
        help_text="Upload a profile photo.",
    )

    class Meta:
        model = Student
        fields = [
            "admission_number",
            "first_name",
            "last_name",
            "gender",
            "date_of_birth",
            "nationality",
            "email",
            "phone",
            "guardian_name",
            "guardian_relationship",
            "guardian_phone",
            "guardian_email",
            "address",
            "current_class",
            "joined_on",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "joined_on": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already in use.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            raise forms.ValidationError("The two passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        student = super().save(commit=False)
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            password=self.cleaned_data["password1"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            email=self.cleaned_data["email"],
        )
        user.profile.role = UserProfile.ROLE_STUDENT
        user.profile.photo = self.cleaned_data.get("photo")
        user.profile.save()
        student.user = user
        if commit:
            student.save()
        return student


class StudentUpdateForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    photo = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"accept": "image/*"}),
        help_text="Upload a new profile photo if needed.",
    )

    class Meta:
        model = Student
        fields = [
            "admission_number",
            "first_name",
            "last_name",
            "gender",
            "date_of_birth",
            "nationality",
            "email",
            "phone",
            "guardian_name",
            "guardian_relationship",
            "guardian_phone",
            "guardian_email",
            "address",
            "current_class",
            "joined_on",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "joined_on": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["username"].initial = self.instance.user.username
            self.fields["photo"].initial = self.instance.user.profile.photo
        style_form_fields(self)

    def clean_username(self):
        username = self.cleaned_data["username"]
        user_qs = User.objects.filter(username=username)
        if self.instance.pk:
            user_qs = user_qs.exclude(pk=self.instance.user.pk)
        if user_qs.exists():
            raise forms.ValidationError("This username is already in use.")
        return username

    def save(self, commit=True):
        student = super().save(commit=False)
        user = student.user
        user.username = self.cleaned_data["username"]
        user.first_name = student.first_name
        user.last_name = student.last_name
        user.email = student.email
        photo = self.cleaned_data.get("photo")
        if commit:
            user.save()
            if photo:
                user.profile.photo = photo
                user.profile.save()
            student.save()
        return student

```

## students/views.py

```python
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import UserProfile
from accounts.permissions import get_user_role, role_required

from .forms import StudentCreateForm, StudentUpdateForm
from .models import Student


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def student_list_view(request):
    query = request.GET.get("q", "").strip()
    students = Student.objects.select_related("current_class", "user")
    if query:
        students = students.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(admission_number__icontains=query)
            | Q(current_class__name__icontains=query)
        )
    return render(request, "students/student_list.html", {"students": students, "query": query})


@login_required
def student_detail_view(request, pk):
    student = get_object_or_404(Student.objects.select_related("current_class", "user"), pk=pk)
    role = get_user_role(request.user)
    if role == UserProfile.ROLE_STUDENT and student.user != request.user:
        raise PermissionDenied
    if role not in {UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER, UserProfile.ROLE_STUDENT}:
        raise PermissionDenied
    return render(request, "students/student_detail.html", {"student": student})


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def student_create_view(request):
    form = StudentCreateForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            form.save()
        messages.success(request, "Student created successfully.")
        return redirect("students:list")
    return render(
        request,
        "students/student_form.html",
        {"form": form, "page_title": "Add Student", "submit_label": "Save Student"},
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def student_update_view(request, pk):
    student = get_object_or_404(Student, pk=pk)
    form = StudentUpdateForm(request.POST or None, request.FILES or None, instance=student)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            form.save()
        messages.success(request, "Student updated successfully.")
        return redirect("students:detail", pk=student.pk)
    return render(
        request,
        "students/student_form.html",
        {"form": form, "page_title": "Update Student", "submit_label": "Update Student"},
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def student_delete_view(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == "POST":
        student.user.delete()
        messages.success(request, "Student deleted successfully.")
        return redirect("students:list")
    return render(request, "students/student_confirm_delete.html", {"student": student})

```

## students/urls.py

```python
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

```

## students/admin.py

```python
from django.contrib import admin

from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("admission_number", "first_name", "last_name", "current_class", "joined_on")
    list_filter = ("gender", "current_class")
    search_fields = ("admission_number", "first_name", "last_name", "email")

```

## teachers/models.py

```python
from django.contrib.auth.models import User
from django.db import models


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="teacher_profile")
    employee_id = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    nationality = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    specialization = models.CharField(max_length=150, blank=True)
    qualifications = models.TextField(blank=True)
    department = models.CharField(max_length=150, blank=True)
    position = models.CharField(max_length=150, blank=True)
    address = models.TextField(blank=True)
    hired_on = models.DateField()

    class Meta:
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.employee_id} - {self.full_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

```

## teachers/forms.py

```python
from django import forms
from django.contrib.auth.models import User

from accounts.form_utils import style_form_fields
from accounts.models import UserProfile

from .models import Teacher


class TeacherCreateForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    password1 = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(widget=forms.PasswordInput())
    photo = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"accept": "image/*"}),
        help_text="Upload a profile photo.",
    )

    class Meta:
        model = Teacher
        fields = [
            "employee_id",
            "first_name",
            "last_name",
            "nationality",
            "email",
            "phone",
            "specialization",
            "qualifications",
            "department",
            "position",
            "address",
            "hired_on",
        ]
        widgets = {
            "hired_on": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 3}),
            "qualifications": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already in use.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            raise forms.ValidationError("The two passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        teacher = super().save(commit=False)
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            password=self.cleaned_data["password1"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            email=self.cleaned_data["email"],
        )
        user.profile.role = UserProfile.ROLE_TEACHER
        user.profile.photo = self.cleaned_data.get("photo")
        user.profile.save()
        teacher.user = user
        if commit:
            teacher.save()
        return teacher


class TeacherUpdateForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    photo = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"accept": "image/*"}),
        help_text="Upload a new profile photo if needed.",
    )

    class Meta:
        model = Teacher
        fields = [
            "employee_id",
            "first_name",
            "last_name",
            "nationality",
            "email",
            "phone",
            "specialization",
            "qualifications",
            "department",
            "position",
            "address",
            "hired_on",
        ]
        widgets = {
            "hired_on": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 3}),
            "qualifications": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["username"].initial = self.instance.user.username
            self.fields["photo"].initial = self.instance.user.profile.photo
        style_form_fields(self)

    def clean_username(self):
        username = self.cleaned_data["username"]
        user_qs = User.objects.filter(username=username)
        if self.instance.pk:
            user_qs = user_qs.exclude(pk=self.instance.user.pk)
        if user_qs.exists():
            raise forms.ValidationError("This username is already in use.")
        return username

    def save(self, commit=True):
        teacher = super().save(commit=False)
        user = teacher.user
        user.username = self.cleaned_data["username"]
        user.first_name = teacher.first_name
        user.last_name = teacher.last_name
        user.email = teacher.email
        photo = self.cleaned_data.get("photo")
        if commit:
            user.save()
            if photo:
                user.profile.photo = photo
                user.profile.save()
            teacher.save()
        return teacher

```

## teachers/views.py

```python
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import UserProfile
from accounts.permissions import get_user_role, role_required

from .forms import TeacherCreateForm, TeacherUpdateForm
from .models import Teacher


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def teacher_list_view(request):
    query = request.GET.get("q", "").strip()
    teachers = Teacher.objects.select_related("user")
    if query:
        teachers = teachers.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(employee_id__icontains=query)
            | Q(specialization__icontains=query)
        )
    return render(request, "teachers/teacher_list.html", {"teachers": teachers, "query": query})


@login_required
def teacher_detail_view(request, pk):
    teacher = get_object_or_404(Teacher.objects.select_related("user"), pk=pk)
    role = get_user_role(request.user)
    if role == UserProfile.ROLE_TEACHER and teacher.user != request.user:
        raise PermissionDenied
    if role not in {UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER}:
        raise PermissionDenied
    return render(request, "teachers/teacher_detail.html", {"teacher": teacher})


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def teacher_create_view(request):
    form = TeacherCreateForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            form.save()
        messages.success(request, "Teacher created successfully.")
        return redirect("teachers:list")
    return render(
        request,
        "teachers/teacher_form.html",
        {"form": form, "page_title": "Add Teacher", "submit_label": "Save Teacher"},
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def teacher_update_view(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    form = TeacherUpdateForm(request.POST or None, request.FILES or None, instance=teacher)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            form.save()
        messages.success(request, "Teacher updated successfully.")
        return redirect("teachers:detail", pk=teacher.pk)
    return render(
        request,
        "teachers/teacher_form.html",
        {"form": form, "page_title": "Update Teacher", "submit_label": "Update Teacher"},
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def teacher_delete_view(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == "POST":
        teacher.user.delete()
        messages.success(request, "Teacher deleted successfully.")
        return redirect("teachers:list")
    return render(request, "teachers/teacher_confirm_delete.html", {"teacher": teacher})

```

## teachers/urls.py

```python
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

```

## teachers/admin.py

```python
from django.contrib import admin

from .models import Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "first_name", "last_name", "specialization", "hired_on")
    list_filter = ("specialization",)
    search_fields = ("employee_id", "first_name", "last_name", "email")

```

## academics/models.py

```python
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class SchoolClass(models.Model):
    name = models.CharField(max_length=100)
    section = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    class_teacher = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_classes",
    )

    class Meta:
        ordering = ["name", "section"]
        constraints = [
            models.UniqueConstraint(fields=["name", "section"], name="unique_class_name_and_section"),
        ]

    def __str__(self):
        return f"{self.name} {self.section}".strip()

    @property
    def student_count(self):
        return self.enrolled_students.count()


class Subject(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class TeachingAssignment(models.Model):
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="teaching_assignments")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="teaching_assignments")
    teacher = models.ForeignKey("teachers.Teacher", on_delete=models.CASCADE, related_name="teaching_assignments")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["school_class__name", "subject__name"]
        constraints = [
            models.UniqueConstraint(fields=["school_class", "subject"], name="unique_class_subject_assignment"),
        ]

    def __str__(self):
        return f"{self.school_class} - {self.subject.name} ({self.teacher.full_name})"


class AttendanceRecord(models.Model):
    STATUS_PRESENT = "Present"
    STATUS_ABSENT = "Absent"
    STATUS_LATE = "Late"
    STATUS_EXCUSED = "Excused"

    STATUS_CHOICES = (
        (STATUS_PRESENT, "Present"),
        (STATUS_ABSENT, "Absent"),
        (STATUS_LATE, "Late"),
        (STATUS_EXCUSED, "Excused"),
    )

    date = models.DateField()
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="attendance_records")
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="attendance_records")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PRESENT)
    note = models.CharField(max_length=255, blank=True)
    marked_by = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marked_attendance",
    )

    class Meta:
        ordering = ["-date", "student__first_name", "student__last_name"]
        constraints = [
            models.UniqueConstraint(fields=["date", "school_class", "student"], name="unique_daily_attendance"),
        ]

    def __str__(self):
        return f"{self.student.full_name} - {self.date} - {self.status}"


class Grade(models.Model):
    TERM_CHOICES = (
        ("Term 1", "Term 1"),
        ("Term 2", "Term 2"),
        ("Term 3", "Term 3"),
    )

    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="grades")
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="grades")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="grades")
    teacher = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_grades",
    )
    term = models.CharField(max_length=20, choices=TERM_CHOICES)
    ca_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(40)],
        default=0,
    )
    exam_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(60)],
        default=0,
    )
    remarks = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["student__first_name", "subject__name"]
        constraints = [
            models.UniqueConstraint(fields=["student", "subject", "term"], name="unique_student_subject_term_grade"),
        ]

    def __str__(self):
        return f"{self.student.full_name} - {self.subject.name} - {self.term}"

    @property
    def total_score(self):
        return float(self.ca_score) + float(self.exam_score)

    @property
    def letter_grade(self):
        total = self.total_score
        if total >= 80:
            return "A"
        if total >= 70:
            return "B"
        if total >= 60:
            return "C"
        if total >= 50:
            return "D"
        return "F"

```

## academics/forms.py

```python
from datetime import date

from django import forms

from accounts.form_utils import style_form_fields

from .models import Grade, SchoolClass, Subject, TeachingAssignment


class SchoolClassForm(forms.ModelForm):
    class Meta:
        model = SchoolClass
        fields = ["name", "section", "description", "class_teacher"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["code", "name", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)


class TeachingAssignmentForm(forms.ModelForm):
    class Meta:
        model = TeachingAssignment
        fields = ["school_class", "subject", "teacher"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)


class AttendanceSelectionForm(forms.Form):
    school_class = forms.ModelChoiceField(queryset=SchoolClass.objects.none())
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), initial=date.today)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["school_class"].queryset = SchoolClass.objects.select_related("class_teacher")
        style_form_fields(self)


class GradeUploadForm(forms.Form):
    school_class = forms.ModelChoiceField(queryset=SchoolClass.objects.none())
    subject = forms.ModelChoiceField(queryset=Subject.objects.none())
    term = forms.ChoiceField(choices=[("", "Select term"), *Grade.TERM_CHOICES])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["school_class"].queryset = SchoolClass.objects.select_related("class_teacher")
        self.fields["subject"].queryset = Subject.objects.all()
        style_form_fields(self)

```

## academics/views.py

```python
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from accounts.models import UserProfile
from accounts.permissions import get_user_role, role_required
from students.models import Student

from .forms import AttendanceSelectionForm, GradeUploadForm, SchoolClassForm, SubjectForm, TeachingAssignmentForm
from .models import AttendanceRecord, Grade, SchoolClass, Subject, TeachingAssignment


def safe_decimal(value, upper_limit):
    try:
        decimal_value = Decimal(str(value or "0"))
    except InvalidOperation:
        decimal_value = Decimal("0")
    return max(Decimal("0"), min(Decimal(str(upper_limit)), decimal_value))


def teacher_can_access_class(user, school_class):
    teacher = getattr(user, "teacher_profile", None)
    if not teacher:
        return False
    return school_class.class_teacher_id == teacher.id or TeachingAssignment.objects.filter(
        teacher=teacher,
        school_class=school_class,
    ).exists()


def teacher_can_upload_subject_grade(user, school_class, subject):
    teacher = getattr(user, "teacher_profile", None)
    if not teacher:
        return False
    return TeachingAssignment.objects.filter(teacher=teacher, school_class=school_class, subject=subject).exists()


def configure_assignment_form_for_user(request, form):
    if get_user_role(request.user) == UserProfile.ROLE_TEACHER:
        teacher = getattr(request.user, "teacher_profile", None)
        if not teacher:
            raise PermissionDenied
        form.fields["teacher"].queryset = form.fields["teacher"].queryset.filter(pk=teacher.pk)
        form.fields["teacher"].initial = teacher
        form.fields["teacher"].help_text = "Teachers can only create and manage their own assignments."
    return form


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def class_list_view(request):
    query = request.GET.get("q", "").strip()
    classes = SchoolClass.objects.select_related("class_teacher")
    if query:
        classes = classes.filter(
            Q(name__icontains=query)
            | Q(section__icontains=query)
            | Q(class_teacher__first_name__icontains=query)
            | Q(class_teacher__last_name__icontains=query)
        )
    return render(request, "academics/class_list.html", {"classes": classes, "query": query})


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def class_create_view(request):
    form = SchoolClassForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Class created successfully.")
        return redirect("academics:class_list")
    return render(
        request,
        "academics/class_form.html",
        {"form": form, "page_title": "Create Class", "submit_label": "Save Class"},
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def class_update_view(request, pk):
    school_class = get_object_or_404(SchoolClass, pk=pk)
    form = SchoolClassForm(request.POST or None, instance=school_class)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Class updated successfully.")
        return redirect("academics:class_list")
    return render(
        request,
        "academics/class_form.html",
        {"form": form, "page_title": "Update Class", "submit_label": "Update Class"},
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def class_delete_view(request, pk):
    school_class = get_object_or_404(SchoolClass, pk=pk)
    if request.method == "POST":
        school_class.delete()
        messages.success(request, "Class deleted successfully.")
        return redirect("academics:class_list")
    return render(request, "academics/class_confirm_delete.html", {"school_class": school_class})


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def subject_list_view(request):
    query = request.GET.get("q", "").strip()
    subjects = Subject.objects.all()
    if query:
        subjects = subjects.filter(Q(name__icontains=query) | Q(code__icontains=query))
    return render(request, "academics/subject_list.html", {"subjects": subjects, "query": query})


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def subject_create_view(request):
    form = SubjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Subject created successfully.")
        return redirect("academics:subject_list")
    return render(
        request,
        "academics/subject_form.html",
        {"form": form, "page_title": "Create Subject", "submit_label": "Save Subject"},
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def subject_update_view(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    form = SubjectForm(request.POST or None, instance=subject)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Subject updated successfully.")
        return redirect("academics:subject_list")
    return render(
        request,
        "academics/subject_form.html",
        {"form": form, "page_title": "Update Subject", "submit_label": "Update Subject"},
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def subject_delete_view(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == "POST":
        subject.delete()
        messages.success(request, "Subject deleted successfully.")
        return redirect("academics:subject_list")
    return render(request, "academics/subject_confirm_delete.html", {"subject": subject})


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def assignment_list_view(request):
    assignments = TeachingAssignment.objects.select_related("teacher", "subject", "school_class")
    if get_user_role(request.user) == UserProfile.ROLE_TEACHER:
        assignments = assignments.filter(teacher=getattr(request.user, "teacher_profile", None))
    return render(request, "academics/assignment_list.html", {"assignments": assignments})


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def assignment_create_view(request):
    form = TeachingAssignmentForm(request.POST or None)
    form = configure_assignment_form_for_user(request, form)
    if request.method == "POST" and form.is_valid():
        assignment = form.save(commit=False)
        if get_user_role(request.user) == UserProfile.ROLE_TEACHER:
            assignment.teacher = getattr(request.user, "teacher_profile", None)
        assignment.save()
        messages.success(request, "Teacher assignment created successfully.")
        return redirect("academics:assignment_list")
    return render(
        request,
        "academics/assignment_form.html",
        {"form": form, "page_title": "Assign Teacher", "submit_label": "Save Assignment"},
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def assignment_update_view(request, pk):
    assignment = get_object_or_404(TeachingAssignment, pk=pk)
    if get_user_role(request.user) == UserProfile.ROLE_TEACHER and assignment.teacher != getattr(
        request.user,
        "teacher_profile",
        None,
    ):
        raise PermissionDenied
    form = TeachingAssignmentForm(request.POST or None, instance=assignment)
    form = configure_assignment_form_for_user(request, form)
    if request.method == "POST" and form.is_valid():
        assignment = form.save(commit=False)
        if get_user_role(request.user) == UserProfile.ROLE_TEACHER:
            assignment.teacher = getattr(request.user, "teacher_profile", None)
        assignment.save()
        messages.success(request, "Teacher assignment updated successfully.")
        return redirect("academics:assignment_list")
    return render(
        request,
        "academics/assignment_form.html",
        {"form": form, "page_title": "Update Assignment", "submit_label": "Update Assignment"},
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def assignment_delete_view(request, pk):
    assignment = get_object_or_404(TeachingAssignment, pk=pk)
    if get_user_role(request.user) == UserProfile.ROLE_TEACHER and assignment.teacher != getattr(
        request.user,
        "teacher_profile",
        None,
    ):
        raise PermissionDenied
    if request.method == "POST":
        assignment.delete()
        messages.success(request, "Teacher assignment deleted successfully.")
        return redirect("academics:assignment_list")
    return render(request, "academics/assignment_confirm_delete.html", {"assignment": assignment})


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def attendance_mark_view(request):
    form_source = request.POST if request.method == "POST" else request.GET or None
    form = AttendanceSelectionForm(form_source)
    attendance_rows = []
    selected_class = None
    selected_date = None

    if form.is_valid():
        selected_class = form.cleaned_data["school_class"]
        selected_date = form.cleaned_data["date"]
        if get_user_role(request.user) == UserProfile.ROLE_TEACHER and not teacher_can_access_class(request.user, selected_class):
            raise PermissionDenied

        students = Student.objects.filter(current_class=selected_class).order_by("first_name", "last_name")
        existing_records = {
            record.student_id: record
            for record in AttendanceRecord.objects.filter(school_class=selected_class, date=selected_date)
        }
        attendance_rows = [
            {
                "student": student,
                "status": existing_records.get(student.id).status if student.id in existing_records else AttendanceRecord.STATUS_PRESENT,
                "note": existing_records.get(student.id).note if student.id in existing_records else "",
            }
            for student in students
        ]

        if request.method == "POST":
            teacher = getattr(request.user, "teacher_profile", None)
            for row in attendance_rows:
                status = request.POST.get(f"status_{row['student'].id}", AttendanceRecord.STATUS_PRESENT)
                note = request.POST.get(f"note_{row['student'].id}", "")
                AttendanceRecord.objects.update_or_create(
                    date=selected_date,
                    school_class=selected_class,
                    student=row["student"],
                    defaults={"status": status, "note": note, "marked_by": teacher},
                )
            messages.success(request, "Attendance saved successfully.")
            redirect_url = f"{reverse('academics:attendance_mark')}?school_class={selected_class.pk}&date={selected_date.isoformat()}"
            return redirect(redirect_url)

    return render(
        request,
        "academics/attendance_form.html",
        {
            "form": form,
            "attendance_rows": attendance_rows,
            "selected_class": selected_class,
            "selected_date": selected_date,
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def attendance_records_view(request):
    form = AttendanceSelectionForm(request.GET or None)
    records = AttendanceRecord.objects.select_related("student", "school_class", "marked_by")
    if form.is_valid():
        school_class = form.cleaned_data["school_class"]
        date_value = form.cleaned_data["date"]
        if get_user_role(request.user) == UserProfile.ROLE_TEACHER and not teacher_can_access_class(request.user, school_class):
            raise PermissionDenied
        records = records.filter(school_class=school_class, date=date_value)
    else:
        records = records.none()

    return render(request, "academics/attendance_list.html", {"form": form, "records": records})


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def grade_upload_view(request):
    form_source = request.POST if request.method == "POST" else request.GET or None
    form = GradeUploadForm(form_source)
    grade_rows = []
    selected_class = None
    selected_subject = None
    selected_term = None

    if form.is_valid():
        selected_class = form.cleaned_data["school_class"]
        selected_subject = form.cleaned_data["subject"]
        selected_term = form.cleaned_data["term"]
        if get_user_role(request.user) == UserProfile.ROLE_TEACHER and not teacher_can_upload_subject_grade(
            request.user,
            selected_class,
            selected_subject,
        ):
            raise PermissionDenied

        students = Student.objects.filter(current_class=selected_class).order_by("first_name", "last_name")
        existing_grades = {
            grade.student_id: grade
            for grade in Grade.objects.filter(
                school_class=selected_class,
                subject=selected_subject,
                term=selected_term,
            )
        }
        grade_rows = [
            {
                "student": student,
                "ca_score": existing_grades.get(student.id).ca_score if student.id in existing_grades else 0,
                "exam_score": existing_grades.get(student.id).exam_score if student.id in existing_grades else 0,
                "remarks": existing_grades.get(student.id).remarks if student.id in existing_grades else "",
                "total_score": existing_grades.get(student.id).total_score if student.id in existing_grades else 0,
            }
            for student in students
        ]

        if request.method == "POST":
            teacher = getattr(request.user, "teacher_profile", None)
            for row in grade_rows:
                student = row["student"]
                ca_score = safe_decimal(request.POST.get(f"ca_{student.id}", "0"), 40)
                exam_score = safe_decimal(request.POST.get(f"exam_{student.id}", "0"), 60)
                remarks = request.POST.get(f"remarks_{student.id}", "")
                Grade.objects.update_or_create(
                    student=student,
                    subject=selected_subject,
                    term=selected_term,
                    defaults={
                        "school_class": selected_class,
                        "teacher": teacher,
                        "ca_score": ca_score,
                        "exam_score": exam_score,
                        "remarks": remarks,
                    },
                )
            messages.success(request, "Grades uploaded successfully.")
            redirect_url = "{}?{}".format(
                reverse("academics:grade_upload"),
                urlencode(
                    {
                        "school_class": selected_class.pk,
                        "subject": selected_subject.pk,
                        "term": selected_term,
                    }
                ),
            )
            return redirect(redirect_url)

    return render(
        request,
        "academics/grade_form.html",
        {
            "form": form,
            "grade_rows": grade_rows,
            "selected_class": selected_class,
            "selected_subject": selected_subject,
            "selected_term": selected_term,
        },
    )


@login_required
def grade_list_view(request):
    role = get_user_role(request.user)
    term = request.GET.get("term", "").strip()
    grades = Grade.objects.select_related("student", "subject", "school_class", "teacher")

    if role == UserProfile.ROLE_STUDENT:
        grades = grades.filter(student=getattr(request.user, "student_profile", None))
    elif role == UserProfile.ROLE_TEACHER:
        grades = grades.filter(teacher=getattr(request.user, "teacher_profile", None))
    elif role != UserProfile.ROLE_ADMIN:
        raise PermissionDenied

    if term:
        grades = grades.filter(term=term)

    return render(
        request,
        "academics/grade_list.html",
        {"grades": grades, "term": term, "term_choices": Grade.TERM_CHOICES},
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def grade_delete_view(request, pk):
    grade = get_object_or_404(Grade.objects.select_related("teacher"), pk=pk)
    if get_user_role(request.user) == UserProfile.ROLE_TEACHER and grade.teacher != getattr(request.user, "teacher_profile", None):
        raise PermissionDenied
    if request.method == "POST":
        grade.delete()
        messages.success(request, "Grade record deleted successfully.")
        return redirect("academics:grade_list")
    return render(request, "academics/grade_confirm_delete.html", {"grade": grade})

```

## academics/urls.py

```python
from django.urls import path

from . import views

app_name = "academics"

urlpatterns = [
    path("classes/", views.class_list_view, name="class_list"),
    path("classes/add/", views.class_create_view, name="class_add"),
    path("classes/<int:pk>/edit/", views.class_update_view, name="class_edit"),
    path("classes/<int:pk>/delete/", views.class_delete_view, name="class_delete"),
    path("subjects/", views.subject_list_view, name="subject_list"),
    path("subjects/add/", views.subject_create_view, name="subject_add"),
    path("subjects/<int:pk>/edit/", views.subject_update_view, name="subject_edit"),
    path("subjects/<int:pk>/delete/", views.subject_delete_view, name="subject_delete"),
    path("assignments/", views.assignment_list_view, name="assignment_list"),
    path("assignments/add/", views.assignment_create_view, name="assignment_add"),
    path("assignments/<int:pk>/edit/", views.assignment_update_view, name="assignment_edit"),
    path("assignments/<int:pk>/delete/", views.assignment_delete_view, name="assignment_delete"),
    path("attendance/mark/", views.attendance_mark_view, name="attendance_mark"),
    path("attendance/records/", views.attendance_records_view, name="attendance_records"),
    path("grades/upload/", views.grade_upload_view, name="grade_upload"),
    path("grades/", views.grade_list_view, name="grade_list"),
    path("grades/<int:pk>/delete/", views.grade_delete_view, name="grade_delete"),
]

```

## academics/admin.py

```python
from django.contrib import admin

from .models import AttendanceRecord, Grade, SchoolClass, Subject, TeachingAssignment


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ("name", "section", "class_teacher")
    search_fields = ("name", "section")


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


@admin.register(TeachingAssignment)
class TeachingAssignmentAdmin(admin.ModelAdmin):
    list_display = ("school_class", "subject", "teacher", "created_at")
    list_filter = ("school_class", "subject")


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("date", "school_class", "student", "status", "marked_by")
    list_filter = ("date", "status", "school_class")
    search_fields = ("student__first_name", "student__last_name")


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ("student", "subject", "term", "ca_score", "exam_score", "uploaded_at")
    list_filter = ("term", "subject", "school_class")
    search_fields = ("student__first_name", "student__last_name")

```

## academics/management/commands/seed_school.py

```python
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from academics.models import AttendanceRecord, Grade, SchoolClass, Subject, TeachingAssignment
from accounts.models import StaffRegistration, StudentRegistration, UserProfile
from students.models import Student
from teachers.models import Teacher


class Command(BaseCommand):
    help = "Create sample data for Sim Tech Academy."

    def handle(self, *args, **options):
        today = date.today()
        yesterday = today - timedelta(days=1)

        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "first_name": "System",
                "last_name": "Admin",
                "email": "admin@simtechacademy.com",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin_user.first_name = "System"
        admin_user.last_name = "Admin"
        admin_user.email = "admin@simtechacademy.com"
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.set_password("admin12345")
        admin_user.save()
        admin_user.profile.role = UserProfile.ROLE_ADMIN
        admin_user.profile.save()

        teacher_specs = [
            {
                "username": "mchola",
                "password": "teacher12345",
                "employee_id": "T-1001",
                "first_name": "Martha",
                "last_name": "Chola",
                "nationality": "Zambian",
                "email": "martha@simtechacademy.com",
                "phone": "0977000001",
                "specialization": "Mathematics",
                "qualifications": "Bachelor of Education in Mathematics",
                "department": "Mathematics",
                "position": "Mathematics Teacher",
            },
            {
                "username": "bphiri",
                "password": "teacher12345",
                "employee_id": "T-1002",
                "first_name": "Brian",
                "last_name": "Phiri",
                "nationality": "Zambian",
                "email": "brian@simtechacademy.com",
                "phone": "0977000002",
                "specialization": "Science",
                "qualifications": "Bachelor of Science with Education",
                "department": "Science",
                "position": "Science Teacher",
            },
            {
                "username": "nlungu",
                "password": "teacher12345",
                "employee_id": "T-1003",
                "first_name": "Naomi",
                "last_name": "Lungu",
                "nationality": "Zambian",
                "email": "naomi@simtechacademy.com",
                "phone": "0977000003",
                "specialization": "English",
                "qualifications": "Bachelor of Arts in English",
                "department": "Languages",
                "position": "English Teacher",
            },
        ]

        teachers = {}
        for spec in teacher_specs:
            user, _ = User.objects.get_or_create(
                username=spec["username"],
                defaults={
                    "first_name": spec["first_name"],
                    "last_name": spec["last_name"],
                    "email": spec["email"],
                },
            )
            user.first_name = spec["first_name"]
            user.last_name = spec["last_name"]
            user.email = spec["email"]
            user.set_password(spec["password"])
            user.save()
            user.profile.role = UserProfile.ROLE_TEACHER
            user.profile.save()

            teacher, _ = Teacher.objects.get_or_create(
                user=user,
                defaults={
                    "employee_id": spec["employee_id"],
                    "first_name": spec["first_name"],
                    "last_name": spec["last_name"],
                    "nationality": spec["nationality"],
                    "email": spec["email"],
                    "phone": spec["phone"],
                    "specialization": spec["specialization"],
                    "qualifications": spec["qualifications"],
                    "department": spec["department"],
                    "position": spec["position"],
                    "address": "Lusaka, Zambia",
                    "hired_on": today - timedelta(days=400),
                },
            )
            teacher.employee_id = spec["employee_id"]
            teacher.first_name = spec["first_name"]
            teacher.last_name = spec["last_name"]
            teacher.nationality = spec["nationality"]
            teacher.email = spec["email"]
            teacher.phone = spec["phone"]
            teacher.specialization = spec["specialization"]
            teacher.qualifications = spec["qualifications"]
            teacher.department = spec["department"]
            teacher.position = spec["position"]
            teacher.address = "Lusaka, Zambia"
            teacher.hired_on = today - timedelta(days=400)
            teacher.save()
            teachers[spec["employee_id"]] = teacher

        class_specs = [
            {
                "key": "grade8a",
                "name": "Grade 8",
                "section": "A",
                "description": "Junior secondary class for foundational STEM work.",
                "class_teacher": teachers["T-1001"],
            },
            {
                "key": "grade9a",
                "name": "Grade 9",
                "section": "A",
                "description": "Upper junior class with project-based learning.",
                "class_teacher": teachers["T-1002"],
            },
        ]

        classes = {}
        for spec in class_specs:
            school_class, _ = SchoolClass.objects.get_or_create(
                name=spec["name"],
                section=spec["section"],
                defaults={
                    "description": spec["description"],
                    "class_teacher": spec["class_teacher"],
                },
            )
            school_class.description = spec["description"]
            school_class.class_teacher = spec["class_teacher"]
            school_class.save()
            classes[spec["key"]] = school_class

        subject_specs = [
            {"code": "MTH101", "name": "Mathematics", "description": "Core mathematics subject."},
            {"code": "SCI101", "name": "Integrated Science", "description": "Science concepts and lab work."},
            {"code": "ENG101", "name": "English Language", "description": "Language and comprehension skills."},
        ]

        subjects = {}
        for spec in subject_specs:
            subject, _ = Subject.objects.get_or_create(
                code=spec["code"],
                defaults={"name": spec["name"], "description": spec["description"]},
            )
            subject.name = spec["name"]
            subject.description = spec["description"]
            subject.save()
            subjects[spec["code"]] = subject

        assignment_specs = [
            ("grade8a", "MTH101", "T-1001"),
            ("grade8a", "SCI101", "T-1002"),
            ("grade8a", "ENG101", "T-1003"),
            ("grade9a", "MTH101", "T-1001"),
            ("grade9a", "SCI101", "T-1002"),
            ("grade9a", "ENG101", "T-1003"),
        ]

        for class_key, subject_code, teacher_id in assignment_specs:
            TeachingAssignment.objects.update_or_create(
                school_class=classes[class_key],
                subject=subjects[subject_code],
                defaults={"teacher": teachers[teacher_id]},
            )

        student_specs = [
            {
                "username": "sianthony",
                "password": "student12345",
                "admission_number": "STA-001",
                "first_name": "Ian",
                "last_name": "Anthony",
                "gender": "Male",
                "nationality": "Zambian",
                "email": "ian@student.simtechacademy.com",
                "phone": "0966000001",
                "guardian_name": "Mr Anthony",
                "guardian_relationship": "Father",
                "guardian_phone": "0978000001",
                "guardian_email": "anthony.guardian@example.com",
                "current_class": classes["grade8a"],
            },
            {
                "username": "slinda",
                "password": "student12345",
                "admission_number": "STA-002",
                "first_name": "Linda",
                "last_name": "Banda",
                "gender": "Female",
                "nationality": "Zambian",
                "email": "linda@student.simtechacademy.com",
                "phone": "0966000002",
                "guardian_name": "Mrs Banda",
                "guardian_relationship": "Mother",
                "guardian_phone": "0978000002",
                "guardian_email": "banda.guardian@example.com",
                "current_class": classes["grade8a"],
            },
            {
                "username": "smark",
                "password": "student12345",
                "admission_number": "STA-003",
                "first_name": "Mark",
                "last_name": "Zulu",
                "gender": "Male",
                "nationality": "Zambian",
                "email": "mark@student.simtechacademy.com",
                "phone": "0966000003",
                "guardian_name": "Mrs Zulu",
                "guardian_relationship": "Aunt",
                "guardian_phone": "0978000003",
                "guardian_email": "zulu.guardian@example.com",
                "current_class": classes["grade9a"],
            },
            {
                "username": "schipo",
                "password": "student12345",
                "admission_number": "STA-004",
                "first_name": "Chipo",
                "last_name": "Tembo",
                "gender": "Female",
                "nationality": "Zambian",
                "email": "chipo@student.simtechacademy.com",
                "phone": "0966000004",
                "guardian_name": "Mr Tembo",
                "guardian_relationship": "Father",
                "guardian_phone": "0978000004",
                "guardian_email": "tembo.guardian@example.com",
                "current_class": classes["grade9a"],
            },
        ]

        students = {}
        for index, spec in enumerate(student_specs, start=1):
            user, _ = User.objects.get_or_create(
                username=spec["username"],
                defaults={
                    "first_name": spec["first_name"],
                    "last_name": spec["last_name"],
                    "email": spec["email"],
                },
            )
            user.first_name = spec["first_name"]
            user.last_name = spec["last_name"]
            user.email = spec["email"]
            user.set_password(spec["password"])
            user.save()
            user.profile.role = UserProfile.ROLE_STUDENT
            user.profile.save()

            student, _ = Student.objects.get_or_create(
                user=user,
                defaults={
                    "admission_number": spec["admission_number"],
                    "first_name": spec["first_name"],
                    "last_name": spec["last_name"],
                    "gender": spec["gender"],
                    "date_of_birth": today - timedelta(days=365 * (13 + index)),
                    "nationality": spec["nationality"],
                    "email": spec["email"],
                    "phone": spec["phone"],
                    "guardian_name": spec["guardian_name"],
                    "guardian_relationship": spec["guardian_relationship"],
                    "guardian_phone": spec["guardian_phone"],
                    "guardian_email": spec["guardian_email"],
                    "address": "Lusaka, Zambia",
                    "current_class": spec["current_class"],
                    "joined_on": today - timedelta(days=120),
                },
            )
            student.admission_number = spec["admission_number"]
            student.first_name = spec["first_name"]
            student.last_name = spec["last_name"]
            student.gender = spec["gender"]
            student.date_of_birth = today - timedelta(days=365 * (13 + index))
            student.nationality = spec["nationality"]
            student.email = spec["email"]
            student.phone = spec["phone"]
            student.guardian_name = spec["guardian_name"]
            student.guardian_relationship = spec["guardian_relationship"]
            student.guardian_phone = spec["guardian_phone"]
            student.guardian_email = spec["guardian_email"]
            student.address = "Lusaka, Zambia"
            student.current_class = spec["current_class"]
            student.joined_on = today - timedelta(days=120)
            student.save()
            students[spec["admission_number"]] = student

        attendance_specs = [
            (today, classes["grade8a"], students["STA-001"], AttendanceRecord.STATUS_PRESENT, teachers["T-1001"]),
            (today, classes["grade8a"], students["STA-002"], AttendanceRecord.STATUS_LATE, teachers["T-1001"]),
            (today, classes["grade9a"], students["STA-003"], AttendanceRecord.STATUS_PRESENT, teachers["T-1002"]),
            (today, classes["grade9a"], students["STA-004"], AttendanceRecord.STATUS_ABSENT, teachers["T-1002"]),
            (yesterday, classes["grade8a"], students["STA-001"], AttendanceRecord.STATUS_PRESENT, teachers["T-1001"]),
            (yesterday, classes["grade8a"], students["STA-002"], AttendanceRecord.STATUS_PRESENT, teachers["T-1001"]),
        ]

        for record_date, school_class, student, status, teacher in attendance_specs:
            AttendanceRecord.objects.update_or_create(
                date=record_date,
                school_class=school_class,
                student=student,
                defaults={
                    "status": status,
                    "note": "",
                    "marked_by": teacher,
                },
            )

        grade_specs = [
            (students["STA-001"], classes["grade8a"], subjects["MTH101"], teachers["T-1001"], "Term 1", 32, 52, "Strong effort"),
            (students["STA-001"], classes["grade8a"], subjects["SCI101"], teachers["T-1002"], "Term 1", 30, 50, "Very good"),
            (students["STA-002"], classes["grade8a"], subjects["MTH101"], teachers["T-1001"], "Term 1", 28, 44, "Keep practicing"),
            (students["STA-003"], classes["grade9a"], subjects["ENG101"], teachers["T-1003"], "Term 1", 35, 51, "Excellent communication"),
            (students["STA-004"], classes["grade9a"], subjects["SCI101"], teachers["T-1002"], "Term 1", 26, 41, "Needs lab revision"),
        ]

        for student, school_class, subject, teacher, term, ca_score, exam_score, remarks in grade_specs:
            Grade.objects.update_or_create(
                student=student,
                subject=subject,
                term=term,
                defaults={
                    "school_class": school_class,
                    "teacher": teacher,
                    "ca_score": ca_score,
                    "exam_score": exam_score,
                    "remarks": remarks,
                },
            )

        if not StudentRegistration.objects.filter(status=StudentRegistration.STATUS_PENDING).exists():
            StudentRegistration.objects.create(
                full_name="Lweendo Mwansa",
                date_of_birth=today - timedelta(days=365 * 14),
                nationality="Zambian",
                zambian_phone="0966112233",
                personal_email="lweendo.applicant@example.com",
                guardian_name="Mrs Mwansa",
                guardian_relationship="Mother",
                guardian_phone="0978112233",
                guardian_email="mwansa.guardian@example.com",
                previous_school_attended="Hope Basic School",
                last_grade_completed="Grade 7",
                year_of_completion=today.year - 1,
                target_grade="Grade 8",
            )

        if not StaffRegistration.objects.filter(status=StaffRegistration.STATUS_PENDING).exists():
            StaffRegistration.objects.create(
                full_name="Josephine Kalima",
                nationality="Zambian",
                zambian_phone="0977334455",
                personal_email="jkalima.applicant@example.com",
                qualifications="Bachelor of Education in Science",
                department="Science",
                position_applying_for="Science Teacher",
            )

        self.stdout.write(self.style.SUCCESS("Sim Tech Academy sample data created successfully."))
        self.stdout.write("Admin login: admin / admin12345")
        self.stdout.write("Teacher login: mchola / teacher12345")
        self.stdout.write("Student login: sianthony / student12345")

```

## templates/base.html

```html
{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{{ school_name }}{% endblock %}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700&family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <link href="{% static 'css/style.css' %}" rel="stylesheet">
</head>
<body class="app-shell">
    <div class="app-gradient"></div>
    <div class="d-lg-none mobile-header">
        <button class="btn btn-light btn-sm rounded-pill px-3" type="button" data-bs-toggle="offcanvas" data-bs-target="#mobileSidebar">
            <i class="bi bi-list"></i> Menu
        </button>
        <div class="mobile-school">
            <span class="mobile-school__title">{{ school_name }}</span>
            <span class="mobile-school__subtitle">{{ current_role|title }}</span>
        </div>
    </div>

    <div class="offcanvas offcanvas-start sidebar-offcanvas d-lg-none" tabindex="-1" id="mobileSidebar">
        <div class="offcanvas-header border-bottom">
            <div>
                <div class="brand-mark">ST</div>
                <h5 class="offcanvas-title mt-2">{{ school_name }}</h5>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="offcanvas"></button>
        </div>
        <div class="offcanvas-body">
            {% include "includes/sidebar_links.html" %}
        </div>
    </div>

    <div class="container-fluid">
        <div class="row min-vh-100">
            <aside class="col-lg-2 d-none d-lg-flex sidebar-panel">
                <div class="sidebar-panel__inner w-100">
                    <div class="brand-wrap">
                        <div class="brand-mark">ST</div>
                        <div>
                            <h1 class="brand-title">{{ school_name }}</h1>
                            <p class="brand-copy mb-0">Smart learning administration</p>
                        </div>
                    </div>
                    {% include "includes/sidebar_links.html" %}
                </div>
            </aside>

            <main class="col-lg-10 ms-auto content-panel">
                <div class="content-topbar">
                    <div>
                        <p class="eyebrow mb-1">School management portal</p>
                        <h2 class="page-heading mb-0">{% block page_heading %}Dashboard{% endblock %}</h2>
                    </div>
                    <div class="topbar-actions">
                        <div class="user-chip">
                            <div class="user-chip__meta">
                                <span class="user-chip__name">{{ request.user.get_full_name|default:request.user.username }}</span>
                                <span class="user-chip__role">{{ current_role|title }}</span>
                            </div>
                            <span class="user-chip__icon">
                                {% if request.user.profile.photo %}
                                    <img src="{{ request.user.profile.photo.url }}" alt="{{ request.user.username }}" class="topbar-avatar">
                                {% else %}
                                    <i class="bi bi-person-circle"></i>
                                {% endif %}
                            </span>
                        </div>
                        {% if request.user.is_authenticated %}
                            <a href="{% url 'accounts:logout' %}" class="btn btn-outline-danger rounded-pill logout-btn">
                                <i class="bi bi-box-arrow-right"></i> Logout
                            </a>
                        {% endif %}
                    </div>
                </div>

                {% if messages %}
                    <div class="mb-4">
                        {% for message in messages %}
                            <div class="alert alert-{{ message.tags|default:'info' }} shadow-sm border-0 rounded-4 mb-3">{{ message }}</div>
                        {% endfor %}
                    </div>
                {% endif %}

                {% block content %}{% endblock %}
            </main>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>

```

## templates/includes/sidebar_links.html

```html
<nav class="nav flex-column sidebar-nav">
    <a class="nav-link" href="{% url 'accounts:dashboard' %}">
        <i class="bi bi-speedometer2"></i> Dashboard
    </a>

    {% if current_role == 'admin' or current_role == 'teacher' %}
        <a class="nav-link" href="{% url 'students:list' %}">
            <i class="bi bi-mortarboard"></i> Students
        </a>
        <a class="nav-link" href="{% url 'teachers:list' %}">
            <i class="bi bi-person-badge"></i> Teachers
        </a>
        <a class="nav-link" href="{% url 'academics:class_list' %}">
            <i class="bi bi-building"></i> Classes
        </a>
        <a class="nav-link" href="{% url 'academics:subject_list' %}">
            <i class="bi bi-journal-bookmark"></i> Subjects
        </a>
        <a class="nav-link" href="{% url 'academics:assignment_list' %}">
            <i class="bi bi-diagram-3"></i> Assignments
        </a>
        <a class="nav-link" href="{% url 'academics:attendance_mark' %}">
            <i class="bi bi-calendar-check"></i> Attendance
        </a>
        <a class="nav-link" href="{% url 'academics:grade_upload' %}">
            <i class="bi bi-clipboard-data"></i> Grade Upload
        </a>
    {% endif %}

    <a class="nav-link" href="{% url 'academics:grade_list' %}">
        <i class="bi bi-award"></i> Results
    </a>

    {% if current_role == 'student' and request.user.student_profile %}
        <a class="nav-link" href="{% url 'students:detail' request.user.student_profile.pk %}">
            <i class="bi bi-person-lines-fill"></i> My Profile
        </a>
    {% endif %}

    {% if current_role == 'teacher' and request.user.teacher_profile %}
        <a class="nav-link" href="{% url 'teachers:detail' request.user.teacher_profile.pk %}">
            <i class="bi bi-person-lines-fill"></i> My Profile
        </a>
    {% endif %}

    {% if current_role == 'admin' %}
        <a class="nav-link" href="{% url 'accounts:registration_dashboard' %}">
            <i class="bi bi-person-plus"></i> Registrations
        </a>
        <a class="nav-link" href="/admin/" target="_blank">
            <i class="bi bi-shield-lock"></i> Django Admin
        </a>
    {% endif %}

    {% if current_role == 'admin' or current_role == 'teacher' %}
        <a class="nav-link" href="{% url 'academics:attendance_records' %}">
            <i class="bi bi-card-checklist"></i> Attendance Records
        </a>
    {% endif %}

    <a class="nav-link text-danger-emphasis" href="{% url 'accounts:logout' %}">
        <i class="bi bi-box-arrow-right"></i> Logout
    </a>
</nav>

```

## templates/includes/form_fields.html

```html
{% for field in form %}
    <div class="col-md-6">
        <label class="form-label fw-semibold" for="{{ field.id_for_label }}">{{ field.label }}</label>
        {{ field }}
        {% if field.help_text %}
            <div class="form-text">{{ field.help_text }}</div>
        {% endif %}
        {% for error in field.errors %}
            <div class="text-danger small mt-1">{{ error }}</div>
        {% endfor %}
    </div>
{% endfor %}
{% for error in form.non_field_errors %}
    <div class="col-12">
        <div class="alert alert-danger rounded-4">{{ error }}</div>
    </div>
{% endfor %}

```

## templates/accounts/login.html

```html
{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login | {{ school_name }}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700&family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <link href="{% static 'css/style.css' %}" rel="stylesheet">
</head>
<body class="login-screen">
    <div class="login-backdrop"></div>
    <div class="container py-4 py-lg-5">
        <div class="row justify-content-center align-items-center min-vh-100">
            <div class="col-sm-10 col-md-8 col-lg-5 col-xl-4">
                <div class="login-card">
                    <div class="text-center mb-4">
                        <div class="brand-mark mx-auto mb-3">ST</div>
                        <p class="eyebrow mb-2">Sim Tech Academy</p>
                        <h2 class="mb-1">Welcome Back</h2>
                        <p class="text-muted mb-0">Sign in to continue to {{ school_name }}</p>
                    </div>

                    {% if form.non_field_errors %}
                        <div class="alert alert-danger rounded-4">
                            {% for error in form.non_field_errors %}{{ error }}{% endfor %}
                        </div>
                    {% endif %}

                    {% if messages %}
                        {% for message in messages %}
                            <div class="alert alert-{{ message.tags|default:'info' }} rounded-4">{{ message }}</div>
                        {% endfor %}
                    {% endif %}

                    <form method="post" class="d-grid gap-3">
                        {% csrf_token %}
                        <div>
                            <label class="form-label fw-semibold" for="{{ form.username.id_for_label }}">Username</label>
                            {{ form.username }}
                        </div>
                        <div>
                            <label class="form-label fw-semibold" for="{{ form.password.id_for_label }}">Password</label>
                            {{ form.password }}
                        </div>
                        <button type="submit" class="btn btn-brand btn-lg w-100">Sign In</button>
                    </form>

                    <div class="login-alt-actions">
                        <a href="{% url 'accounts:student_register' %}" class="btn btn-outline-primary rounded-pill w-100">
                            <i class="bi bi-mortarboard"></i> Enroll as Student
                        </a>
                        <a href="{% url 'accounts:staff_register' %}" class="btn btn-outline-secondary rounded-pill w-100">
                            <i class="bi bi-person-workspace"></i> Register as Staff
                        </a>
                    </div>

                    <div class="login-footer">
                        <p class="mb-0">Use your assigned school account to access the portal.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>

```

## templates/accounts/dashboard.html

```html
{% extends "base.html" %}

{% block title %}Dashboard | {{ school_name }}{% endblock %}
{% block page_heading %}Dashboard{% endblock %}

{% block content %}
    <section class="hero-card mb-4">
        <div>
            <span class="eyebrow">School overview</span>
            <h3 class="hero-card__title">Welcome to {{ school_name }}</h3>
            <p class="hero-card__text mb-0">
                {% if current_role == 'admin' %}
                    Monitor student growth, teacher capacity, and class activity from a single control center.
                {% elif current_role == 'teacher' %}
                    Review your teaching assignments, attendance work, and uploaded grade records.
                {% else %}
                    Check your attendance summary and latest subject results from your student dashboard.
                {% endif %}
            </p>
        </div>
        <div class="hero-card__badge">
            <i class="bi bi-bar-chart-line-fill"></i>
        </div>
    </section>

    {% if current_role == 'admin' %}
        <div class="row g-4 mb-4">
            <div class="col-md-6 col-xl-3"><div class="stat-card"><span>Students</span><strong>{{ student_count }}</strong></div></div>
            <div class="col-md-6 col-xl-3"><div class="stat-card"><span>Teachers</span><strong>{{ teacher_count }}</strong></div></div>
            <div class="col-md-6 col-xl-3"><div class="stat-card"><span>Classes</span><strong>{{ class_count }}</strong></div></div>
            <div class="col-md-6 col-xl-3"><div class="stat-card"><span>Subjects</span><strong>{{ subject_count }}</strong></div></div>
            <div class="col-md-6 col-xl-3"><div class="stat-card"><span>Attendance Records</span><strong>{{ attendance_count }}</strong></div></div>
            <div class="col-md-6 col-xl-3"><div class="stat-card"><span>Grade Records</span><strong>{{ grade_count }}</strong></div></div>
            <div class="col-md-6 col-xl-3"><div class="stat-card"><span>Pending Students</span><strong>{{ pending_student_registrations }}</strong></div></div>
            <div class="col-md-6 col-xl-3"><div class="stat-card"><span>Pending Staff</span><strong>{{ pending_staff_registrations }}</strong></div></div>
        </div>

        <div class="row g-4">
            <div class="col-xl-6">
                <div class="content-card h-100">
                    <div class="section-title-wrap">
                        <h4 class="section-title">Recent Grades</h4>
                    </div>
                    <div class="table-responsive">
                        <table class="table align-middle app-table">
                            <thead>
                                <tr><th>Student</th><th>Subject</th><th>Term</th><th>Total</th></tr>
                            </thead>
                            <tbody>
                                {% for grade in recent_grades %}
                                    <tr>
                                        <td>{{ grade.student.full_name }}</td>
                                        <td>{{ grade.subject.name }}</td>
                                        <td>{{ grade.term }}</td>
                                        <td>{{ grade.total_score|floatformat:2 }}</td>
                                    </tr>
                                {% empty %}
                                    <tr><td colspan="4" class="text-center text-muted py-4">No grade records yet.</td></tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            <div class="col-xl-6">
                <div class="content-card h-100 mb-4">
                    <div class="section-title-wrap">
                        <h4 class="section-title">Registration Queue</h4>
                        <a href="{% url 'accounts:registration_dashboard' %}" class="btn btn-brand">Open Queue</a>
                    </div>
                    <div class="profile-grid">
                        <div class="profile-item"><span>Student Applications</span><strong>{{ pending_student_registrations }}</strong></div>
                        <div class="profile-item"><span>Staff Applications</span><strong>{{ pending_staff_registrations }}</strong></div>
                    </div>
                </div>
            </div>
            <div class="col-xl-6">
                <div class="content-card h-100">
                    <div class="section-title-wrap">
                        <h4 class="section-title">Recent Attendance</h4>
                    </div>
                    <div class="table-responsive">
                        <table class="table align-middle app-table">
                            <thead>
                                <tr><th>Date</th><th>Student</th><th>Class</th><th>Status</th></tr>
                            </thead>
                            <tbody>
                                {% for item in recent_attendance %}
                                    <tr>
                                        <td>{{ item.date }}</td>
                                        <td>{{ item.student.full_name }}</td>
                                        <td>{{ item.school_class }}</td>
                                        <td><span class="status-pill">{{ item.status }}</span></td>
                                    </tr>
                                {% empty %}
                                    <tr><td colspan="4" class="text-center text-muted py-4">No attendance records yet.</td></tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    {% elif current_role == 'teacher' %}
        <div class="row g-4 mb-4">
            <div class="col-md-4"><div class="stat-card"><span>Assignments</span><strong>{{ assignment_count }}</strong></div></div>
            <div class="col-md-4"><div class="stat-card"><span>Uploaded Grades</span><strong>{{ grade_count }}</strong></div></div>
            <div class="col-md-4"><div class="stat-card"><span>Attendance Actions</span><strong>{{ attendance_count }}</strong></div></div>
        </div>
        <div class="content-card">
            <div class="section-title-wrap">
                <h4 class="section-title">Your Teaching Assignments</h4>
                <a href="{% url 'academics:grade_upload' %}" class="btn btn-brand">Upload Grades</a>
            </div>
            <div class="table-responsive">
                <table class="table align-middle app-table">
                    <thead>
                        <tr><th>Class</th><th>Subject</th><th>Action</th></tr>
                    </thead>
                    <tbody>
                        {% for assignment in assignments %}
                            <tr>
                                <td>{{ assignment.school_class }}</td>
                                <td>{{ assignment.subject.name }}</td>
                                <td><a class="btn btn-outline-success btn-sm" href="{% url 'academics:grade_upload' %}?school_class={{ assignment.school_class.pk }}&subject={{ assignment.subject.pk }}&term=Term 1">Open Gradebook</a></td>
                            </tr>
                        {% empty %}
                            <tr><td colspan="3" class="text-center text-muted py-4">No assignments available yet.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    {% else %}
        <div class="row g-4 mb-4">
            <div class="col-md-4"><div class="stat-card"><span>My Class</span><strong>{{ student.current_class|default:'Not Assigned' }}</strong></div></div>
            <div class="col-md-4"><div class="stat-card"><span>Result Records</span><strong>{{ grade_count }}</strong></div></div>
            <div class="col-md-4"><div class="stat-card"><span>Attendance Records</span><strong>{{ attendance_count }}</strong></div></div>
        </div>
        <div class="content-card">
            <div class="section-title-wrap">
                <h4 class="section-title">Latest Results</h4>
                <a href="{% url 'academics:grade_list' %}" class="btn btn-brand">View All Results</a>
            </div>
            <div class="table-responsive">
                <table class="table align-middle app-table">
                    <thead>
                        <tr><th>Subject</th><th>Term</th><th>Total</th><th>Grade</th></tr>
                    </thead>
                    <tbody>
                        {% for grade in results %}
                            <tr>
                                <td>{{ grade.subject.name }}</td>
                                <td>{{ grade.term }}</td>
                                <td>{{ grade.total_score|floatformat:2 }}</td>
                                <td><span class="status-pill">{{ grade.letter_grade }}</span></td>
                            </tr>
                        {% empty %}
                            <tr><td colspan="4" class="text-center text-muted py-4">No results uploaded yet.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    {% endif %}
{% endblock %}

```

## templates/accounts/student_registration.html

```html
{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Student Enrollment | {{ school_name }}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700&family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <link href="{% static 'css/style.css' %}" rel="stylesheet">
</head>
<body class="registration-shell">
    <div class="container py-4 py-lg-5">
        <div class="registration-card">
            <div class="section-title-wrap mb-4">
                <div>
                    <p class="eyebrow mb-2">Student Enrollment</p>
                    <h1 class="section-title mb-1">Apply for Admission</h1>
                    <p class="text-muted mb-0">Complete each step. Your account stays inactive until an admin approves the application.</p>
                </div>
                <a href="{% url 'accounts:login' %}" class="btn btn-outline-secondary rounded-pill">Back to Login</a>
            </div>

            <div class="registration-steps mb-4">
                {% for item in step_items %}
                    <div class="registration-step {% if item.is_active %}registration-step--active{% elif item.is_complete %}registration-step--complete{% endif %}">
                        <span class="registration-step__number">{{ item.number }}</span>
                        <div>
                            <strong>{{ item.title }}</strong>
                            <div class="small text-muted">{{ item.key|title }}</div>
                        </div>
                    </div>
                {% endfor %}
            </div>

            <div class="content-card">
                <h3 class="section-title mb-3">{{ current_title }}</h3>
                <form method="post" enctype="multipart/form-data">
                    {% csrf_token %}
                    <input type="hidden" name="current_step" value="{{ current_step }}">
                    <div class="row g-4">
                        {% include "includes/form_fields.html" %}
                    </div>
                    <div class="registration-actions">
                        {% if current_step != step_items.0.key %}
                            <button type="submit" name="action" value="back" class="btn btn-outline-secondary rounded-pill" formnovalidate>Back</button>
                        {% endif %}
                        <button type="submit" class="btn btn-brand">
                            {% if is_final_step %}Submit Enrollment{% else %}Save and Continue{% endif %}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</body>
</html>

```

## templates/accounts/staff_registration.html

```html
{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Staff Registration | {{ school_name }}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700&family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <link href="{% static 'css/style.css' %}" rel="stylesheet">
</head>
<body class="registration-shell">
    <div class="container py-4 py-lg-5">
        <div class="registration-card">
            <div class="section-title-wrap mb-4">
                <div>
                    <p class="eyebrow mb-2">Staff Registration</p>
                    <h1 class="section-title mb-1">Apply to Join the Team</h1>
                    <p class="text-muted mb-0">Submit your details for admin review. Login credentials are only sent after approval.</p>
                </div>
                <a href="{% url 'accounts:login' %}" class="btn btn-outline-secondary rounded-pill">Back to Login</a>
            </div>

            <div class="registration-steps mb-4">
                {% for item in step_items %}
                    <div class="registration-step {% if item.is_active %}registration-step--active{% elif item.is_complete %}registration-step--complete{% endif %}">
                        <span class="registration-step__number">{{ item.number }}</span>
                        <div>
                            <strong>{{ item.title }}</strong>
                            <div class="small text-muted">{{ item.key|title }}</div>
                        </div>
                    </div>
                {% endfor %}
            </div>

            <div class="content-card">
                <h3 class="section-title mb-3">{{ current_title }}</h3>
                <form method="post" enctype="multipart/form-data">
                    {% csrf_token %}
                    <input type="hidden" name="current_step" value="{{ current_step }}">
                    <div class="row g-4">
                        {% include "includes/form_fields.html" %}
                    </div>
                    <div class="registration-actions">
                        {% if current_step != step_items.0.key %}
                            <button type="submit" name="action" value="back" class="btn btn-outline-secondary rounded-pill" formnovalidate>Back</button>
                        {% endif %}
                        <button type="submit" class="btn btn-brand">
                            {% if is_final_step %}Submit Staff Registration{% else %}Save and Continue{% endif %}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</body>
</html>

```

## templates/accounts/registration_success.html

```html
{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Registration Submitted | {{ school_name }}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700&family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="{% static 'css/style.css' %}" rel="stylesheet">
</head>
<body class="registration-shell">
    <div class="container py-5">
        <div class="registration-card registration-card--compact text-center">
            <div class="brand-mark mx-auto mb-3">ST</div>
            <p class="eyebrow mb-2">Submission Received</p>
            <h1 class="section-title mb-3">Registration Submitted</h1>
            {% if notice %}
                <p class="mb-2">Type: <strong>{{ notice.type }}</strong></p>
                <p class="mb-2">Generated ID: <strong>{{ notice.identifier }}</strong></p>
                <p class="text-muted mb-4">Status: {{ notice.status }}. Credentials will only be sent after admin approval.</p>
            {% else %}
                <p class="text-muted mb-4">Your application is now awaiting admin approval.</p>
            {% endif %}
            <div class="d-flex gap-2 justify-content-center flex-wrap">
                <a href="{% url 'accounts:login' %}" class="btn btn-brand">Return to Login</a>
                <a href="{% url 'accounts:student_register' %}" class="btn btn-outline-secondary rounded-pill">New Student Application</a>
            </div>
        </div>
    </div>
</body>
</html>

```

## templates/accounts/registration_dashboard.html

```html
{% extends "base.html" %}

{% block title %}Registrations | {{ school_name }}{% endblock %}
{% block page_heading %}Registrations{% endblock %}

{% block content %}
    <div class="row g-4 mb-4">
        <div class="col-md-6"><div class="stat-card"><span>Pending Student Registrations</span><strong>{{ pending_students|length }}</strong></div></div>
        <div class="col-md-6"><div class="stat-card"><span>Pending Staff Registrations</span><strong>{{ pending_staff|length }}</strong></div></div>
    </div>

    <div class="row g-4">
        <div class="col-xl-6">
            <div class="content-card">
                <h4 class="section-title mb-3">Pending Student Registrations</h4>
                <div class="table-responsive">
                    <table class="table align-middle app-table">
                        <thead>
                            <tr><th>ID</th><th>Name</th><th>Target Grade</th><th>Submitted</th><th>Action</th></tr>
                        </thead>
                        <tbody>
                            {% for item in pending_students %}
                                <tr>
                                    <td>{{ item.student_id }}</td>
                                    <td>{{ item.full_name }}</td>
                                    <td>{{ item.target_grade }}</td>
                                    <td>{{ item.created_at|date:"M d, Y" }}</td>
                                    <td><a href="{% url 'accounts:student_registration_detail' item.pk %}" class="btn btn-outline-primary btn-sm rounded-pill">Review</a></td>
                                </tr>
                            {% empty %}
                                <tr><td colspan="5" class="text-center text-muted py-4">No pending student registrations.</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        <div class="col-xl-6">
            <div class="content-card">
                <h4 class="section-title mb-3">Pending Staff Registrations</h4>
                <div class="table-responsive">
                    <table class="table align-middle app-table">
                        <thead>
                            <tr><th>ID</th><th>Name</th><th>Department</th><th>Submitted</th><th>Action</th></tr>
                        </thead>
                        <tbody>
                            {% for item in pending_staff %}
                                <tr>
                                    <td>{{ item.employee_id }}</td>
                                    <td>{{ item.full_name }}</td>
                                    <td>{{ item.department }}</td>
                                    <td>{{ item.created_at|date:"M d, Y" }}</td>
                                    <td><a href="{% url 'accounts:staff_registration_detail' item.pk %}" class="btn btn-outline-primary btn-sm rounded-pill">Review</a></td>
                                </tr>
                            {% empty %}
                                <tr><td colspan="5" class="text-center text-muted py-4">No pending staff registrations.</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        <div class="col-xl-6">
            <div class="content-card">
                <h4 class="section-title mb-3">Recent Student Decisions</h4>
                <div class="table-responsive">
                    <table class="table align-middle app-table">
                        <thead>
                            <tr><th>ID</th><th>Name</th><th>Status</th><th>Reviewed</th></tr>
                        </thead>
                        <tbody>
                            {% for item in recent_students %}
                                <tr>
                                    <td>{{ item.student_id }}</td>
                                    <td>{{ item.full_name }}</td>
                                    <td><span class="status-pill">{{ item.get_status_display }}</span></td>
                                    <td>{{ item.reviewed_at|default:"-" }}</td>
                                </tr>
                            {% empty %}
                                <tr><td colspan="4" class="text-center text-muted py-4">No reviewed student registrations yet.</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        <div class="col-xl-6">
            <div class="content-card">
                <h4 class="section-title mb-3">Recent Staff Decisions</h4>
                <div class="table-responsive">
                    <table class="table align-middle app-table">
                        <thead>
                            <tr><th>ID</th><th>Name</th><th>Status</th><th>Reviewed</th></tr>
                        </thead>
                        <tbody>
                            {% for item in recent_staff %}
                                <tr>
                                    <td>{{ item.employee_id }}</td>
                                    <td>{{ item.full_name }}</td>
                                    <td><span class="status-pill">{{ item.get_status_display }}</span></td>
                                    <td>{{ item.reviewed_at|default:"-" }}</td>
                                </tr>
                            {% empty %}
                                <tr><td colspan="4" class="text-center text-muted py-4">No reviewed staff registrations yet.</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
{% endblock %}

```

## templates/accounts/student_registration_detail.html

```html
{% extends "base.html" %}

{% block title %}Student Registration Review | {{ school_name }}{% endblock %}
{% block page_heading %}Student Registration Review{% endblock %}

{% block content %}
    <div class="content-card mb-4">
        <div class="section-title-wrap">
            <div>
                <h4 class="section-title">{{ registration.full_name }}</h4>
                <p class="text-muted mb-0">{{ registration.student_id }} | {{ registration.get_status_display }}</p>
            </div>
            <a href="{% url 'accounts:registration_dashboard' %}" class="btn btn-outline-secondary rounded-pill">Back to Queue</a>
        </div>

        <div class="profile-grid">
            <div class="profile-item"><span>Phone</span><strong>{{ registration.zambian_phone }}</strong></div>
            <div class="profile-item"><span>Email</span><strong>{{ registration.personal_email }}</strong></div>
            <div class="profile-item"><span>Date of Birth</span><strong>{{ registration.date_of_birth }}</strong></div>
            <div class="profile-item"><span>Nationality</span><strong>{{ registration.nationality }}</strong></div>
            <div class="profile-item"><span>Target Grade</span><strong>{{ registration.target_grade }}</strong></div>
            <div class="profile-item"><span>Submitted</span><strong>{{ registration.created_at|date:"M d, Y H:i" }}</strong></div>
        </div>
    </div>

    <div class="row g-4">
        <div class="col-xl-7">
            <div class="content-card mb-4">
                <h4 class="section-title mb-3">Guardian Info</h4>
                <div class="profile-grid">
                    <div class="profile-item"><span>Name</span><strong>{{ registration.guardian_name }}</strong></div>
                    <div class="profile-item"><span>Relationship</span><strong>{{ registration.guardian_relationship }}</strong></div>
                    <div class="profile-item"><span>Phone</span><strong>{{ registration.guardian_phone }}</strong></div>
                    <div class="profile-item"><span>Email</span><strong>{{ registration.guardian_email }}</strong></div>
                </div>
            </div>

            <div class="content-card mb-4">
                <h4 class="section-title mb-3">Academic History</h4>
                <div class="profile-grid">
                    <div class="profile-item"><span>Previous School</span><strong>{{ registration.previous_school_attended }}</strong></div>
                    <div class="profile-item"><span>Last Grade Completed</span><strong>{{ registration.last_grade_completed }}</strong></div>
                    <div class="profile-item"><span>Year Completed</span><strong>{{ registration.year_of_completion }}</strong></div>
                </div>
            </div>

            <div class="content-card">
                <h4 class="section-title mb-3">Documents</h4>
                <div class="document-list">
                    {% if registration.last_report_card %}<a href="{{ registration.last_report_card.url }}" target="_blank" class="document-link">Last Report Card</a>{% endif %}
                    {% if registration.birth_certificate %}<a href="{{ registration.birth_certificate.url }}" target="_blank" class="document-link">Birth Certificate</a>{% endif %}
                    {% if registration.transfer_letter %}<a href="{{ registration.transfer_letter.url }}" target="_blank" class="document-link">Transfer Letter</a>{% endif %}
                    {% if registration.profile_photo %}<a href="{{ registration.profile_photo.url }}" target="_blank" class="document-link">Profile Photo</a>{% endif %}
                </div>
            </div>
        </div>

        <div class="col-xl-5">
            <div class="content-card mb-4">
                <h4 class="section-title mb-3">Admin Decision</h4>
                {% if registration.status == 'pending_admin' %}
                    <form method="post" class="d-grid gap-3">
                        {% csrf_token %}
                        <div>
                            <label class="form-label fw-semibold" for="{{ review_form.review_reason.id_for_label }}">Review Note / Rejection Reason</label>
                            {{ review_form.review_reason }}
                        </div>
                        <button type="submit" name="action" value="approve" class="btn btn-brand">Approve and Send Credentials</button>
                        <button type="submit" name="action" value="reject" class="btn btn-outline-danger rounded-pill">Reject Application</button>
                    </form>
                {% else %}
                    <div class="profile-grid">
                        <div class="profile-item"><span>Status</span><strong>{{ registration.get_status_display }}</strong></div>
                        <div class="profile-item"><span>Reviewed By</span><strong>{{ registration.reviewed_by|default:"-" }}</strong></div>
                        <div class="profile-item"><span>Reviewed At</span><strong>{{ registration.reviewed_at|default:"-" }}</strong></div>
                        <div class="profile-item"><span>Approved User</span><strong>{{ registration.approved_user.username|default:"-" }}</strong></div>
                    </div>
                    {% if registration.review_reason %}
                        <div class="alert alert-light border rounded-4 mt-3 mb-0">{{ registration.review_reason }}</div>
                    {% endif %}
                {% endif %}
            </div>

            <div class="content-card">
                <h4 class="section-title mb-3">Notification Log</h4>
                <div class="d-grid gap-3">
                    {% for item in notification_logs %}
                        <div class="profile-item">
                            <span>{{ item.get_channel_display }} - {{ item.get_status_display }}</span>
                            <strong>{{ item.recipient }}</strong>
                            <p class="mb-0 mt-2 text-muted">{{ item.response_message }}</p>
                        </div>
                    {% empty %}
                        <p class="text-muted mb-0">No notifications have been logged yet.</p>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
{% endblock %}

```

## templates/accounts/staff_registration_detail.html

```html
{% extends "base.html" %}

{% block title %}Staff Registration Review | {{ school_name }}{% endblock %}
{% block page_heading %}Staff Registration Review{% endblock %}

{% block content %}
    <div class="content-card mb-4">
        <div class="section-title-wrap">
            <div>
                <h4 class="section-title">{{ registration.full_name }}</h4>
                <p class="text-muted mb-0">{{ registration.employee_id }} | {{ registration.get_status_display }}</p>
            </div>
            <a href="{% url 'accounts:registration_dashboard' %}" class="btn btn-outline-secondary rounded-pill">Back to Queue</a>
        </div>

        <div class="profile-grid">
            <div class="profile-item"><span>Phone</span><strong>{{ registration.zambian_phone }}</strong></div>
            <div class="profile-item"><span>Email</span><strong>{{ registration.personal_email }}</strong></div>
            <div class="profile-item"><span>Nationality</span><strong>{{ registration.nationality }}</strong></div>
            <div class="profile-item"><span>Department</span><strong>{{ registration.department }}</strong></div>
            <div class="profile-item"><span>Position</span><strong>{{ registration.position_applying_for }}</strong></div>
            <div class="profile-item"><span>Submitted</span><strong>{{ registration.created_at|date:"M d, Y H:i" }}</strong></div>
        </div>
    </div>

    <div class="row g-4">
        <div class="col-xl-7">
            <div class="content-card mb-4">
                <h4 class="section-title mb-3">Qualifications</h4>
                <p class="mb-0">{{ registration.qualifications }}</p>
            </div>

            <div class="content-card">
                <h4 class="section-title mb-3">Uploaded Profile Photo</h4>
                {% if registration.profile_photo %}
                    <div class="profile-photo-card profile-photo-card--wide">
                        <img src="{{ registration.profile_photo.url }}" alt="{{ registration.full_name }}" class="profile-photo">
                    </div>
                {% else %}
                    <p class="text-muted mb-0">No profile photo uploaded.</p>
                {% endif %}
            </div>
        </div>

        <div class="col-xl-5">
            <div class="content-card mb-4">
                <h4 class="section-title mb-3">Admin Decision</h4>
                {% if registration.status == 'pending_admin' %}
                    <form method="post" class="d-grid gap-3">
                        {% csrf_token %}
                        <div>
                            <label class="form-label fw-semibold" for="{{ review_form.review_reason.id_for_label }}">Review Note / Rejection Reason</label>
                            {{ review_form.review_reason }}
                        </div>
                        <button type="submit" name="action" value="approve" class="btn btn-brand">Approve and Send Credentials</button>
                        <button type="submit" name="action" value="reject" class="btn btn-outline-danger rounded-pill">Reject Application</button>
                    </form>
                {% else %}
                    <div class="profile-grid">
                        <div class="profile-item"><span>Status</span><strong>{{ registration.get_status_display }}</strong></div>
                        <div class="profile-item"><span>Reviewed By</span><strong>{{ registration.reviewed_by|default:"-" }}</strong></div>
                        <div class="profile-item"><span>Reviewed At</span><strong>{{ registration.reviewed_at|default:"-" }}</strong></div>
                        <div class="profile-item"><span>Approved User</span><strong>{{ registration.approved_user.username|default:"-" }}</strong></div>
                    </div>
                    {% if registration.review_reason %}
                        <div class="alert alert-light border rounded-4 mt-3 mb-0">{{ registration.review_reason }}</div>
                    {% endif %}
                {% endif %}
            </div>

            <div class="content-card">
                <h4 class="section-title mb-3">Notification Log</h4>
                <div class="d-grid gap-3">
                    {% for item in notification_logs %}
                        <div class="profile-item">
                            <span>{{ item.get_channel_display }} - {{ item.get_status_display }}</span>
                            <strong>{{ item.recipient }}</strong>
                            <p class="mb-0 mt-2 text-muted">{{ item.response_message }}</p>
                        </div>
                    {% empty %}
                        <p class="text-muted mb-0">No notifications have been logged yet.</p>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
{% endblock %}

```

## templates/students/student_list.html

```html
{% extends "base.html" %}

{% block title %}Students | {{ school_name }}{% endblock %}
{% block page_heading %}Students{% endblock %}

{% block content %}
    <div class="content-card">
        <div class="search-row">
            <form method="get" class="d-flex gap-2">
                <input type="text" name="q" value="{{ query }}" class="form-control" placeholder="Search by name, admission number, or class">
                <button type="submit" class="btn btn-outline-success rounded-pill px-4">Search</button>
            </form>
            {% if current_role == 'admin' %}
                <a href="{% url 'students:add' %}" class="btn btn-brand">Add Student</a>
            {% endif %}
        </div>

        <div class="table-responsive">
            <table class="table align-middle app-table">
                <thead>
                    <tr>
                        <th>Admission No.</th>
                        <th>Student Name</th>
                        <th>Gender</th>
                        <th>Class</th>
                        <th>Phone</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for student in students %}
                        <tr>
                            <td>{{ student.admission_number }}</td>
                            <td>{{ student.full_name }}</td>
                            <td>{{ student.gender }}</td>
                            <td>{{ student.current_class|default:"Not Assigned" }}</td>
                            <td>{{ student.phone|default:"-" }}</td>
                            <td class="d-flex gap-2 flex-wrap">
                                <a href="{% url 'students:detail' student.pk %}" class="btn btn-outline-success btn-sm rounded-pill">View</a>
                                {% if current_role == 'admin' %}
                                    <a href="{% url 'students:edit' student.pk %}" class="btn btn-outline-secondary btn-sm rounded-pill">Edit</a>
                                    <a href="{% url 'students:delete' student.pk %}" class="btn btn-outline-danger btn-sm rounded-pill">Delete</a>
                                {% endif %}
                            </td>
                        </tr>
                    {% empty %}
                        <tr>
                            <td colspan="6" class="text-center text-muted py-5">No students found.</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
{% endblock %}

```

## templates/students/student_detail.html

```html
{% extends "base.html" %}

{% block title %}Student Profile | {{ school_name }}{% endblock %}
{% block page_heading %}Student Profile{% endblock %}

{% block content %}
    <div class="content-card mb-4">
        <div class="section-title-wrap">
            <div>
                <h4 class="section-title">{{ student.full_name }}</h4>
                <p class="text-muted mb-0">Admission Number: {{ student.admission_number }}</p>
            </div>
            {% if current_role == 'admin' %}
                <div class="d-flex gap-2">
                    <a href="{% url 'students:edit' student.pk %}" class="btn btn-outline-secondary rounded-pill">Edit</a>
                    <a href="{% url 'students:delete' student.pk %}" class="btn btn-outline-danger rounded-pill">Delete</a>
                </div>
            {% endif %}
        </div>

        <div class="profile-layout">
            <div class="profile-photo-card">
                {% if student.user.profile.photo %}
                    <img src="{{ student.user.profile.photo.url }}" alt="{{ student.full_name }}" class="profile-photo">
                {% else %}
                    <div class="profile-photo profile-photo--placeholder">
                        <i class="bi bi-person-circle"></i>
                    </div>
                {% endif %}
            </div>
            <div class="profile-grid">
                <div class="profile-item"><span>Class</span><strong>{{ student.current_class|default:"Not Assigned" }}</strong></div>
                <div class="profile-item"><span>Gender</span><strong>{{ student.gender }}</strong></div>
                <div class="profile-item"><span>Date of Birth</span><strong>{{ student.date_of_birth|default:"-" }}</strong></div>
                <div class="profile-item"><span>Nationality</span><strong>{{ student.nationality|default:"-" }}</strong></div>
                <div class="profile-item"><span>Email</span><strong>{{ student.email|default:"-" }}</strong></div>
                <div class="profile-item"><span>Phone</span><strong>{{ student.phone|default:"-" }}</strong></div>
                <div class="profile-item"><span>Joined On</span><strong>{{ student.joined_on }}</strong></div>
                <div class="profile-item"><span>Username</span><strong>{{ student.user.username }}</strong></div>
            </div>
        </div>
    </div>

    <div class="content-card mb-4">
        <h4 class="section-title mb-3">Guardian Information</h4>
        <div class="profile-grid">
            <div class="profile-item"><span>Guardian Name</span><strong>{{ student.guardian_name|default:"-" }}</strong></div>
            <div class="profile-item"><span>Relationship</span><strong>{{ student.guardian_relationship|default:"-" }}</strong></div>
            <div class="profile-item"><span>Guardian Phone</span><strong>{{ student.guardian_phone|default:"-" }}</strong></div>
            <div class="profile-item"><span>Guardian Email</span><strong>{{ student.guardian_email|default:"-" }}</strong></div>
        </div>
    </div>

    <div class="content-card">
        <h4 class="section-title mb-3">Address</h4>
        <p class="mb-0">{{ student.address|default:"No address supplied yet." }}</p>
    </div>
{% endblock %}

```

## templates/students/student_form.html

```html
{% extends "base.html" %}

{% block title %}{{ page_title }} | {{ school_name }}{% endblock %}
{% block page_heading %}{{ page_title }}{% endblock %}

{% block content %}
    <div class="form-card">
        <form method="post" enctype="multipart/form-data">
            {% csrf_token %}
            <div class="row g-4">
                {% include "includes/form_fields.html" %}
            </div>
            <div class="d-flex gap-2 mt-4">
                <button type="submit" class="btn btn-brand">{{ submit_label }}</button>
                <a href="{% url 'students:list' %}" class="btn btn-outline-secondary rounded-pill">Cancel</a>
            </div>
        </form>
    </div>
{% endblock %}

```

## templates/students/student_confirm_delete.html

```html
{% extends "base.html" %}

{% block title %}Delete Student | {{ school_name }}{% endblock %}
{% block page_heading %}Delete Student{% endblock %}

{% block content %}
    <div class="form-card">
        <h4 class="section-title">Remove {{ student.full_name }}?</h4>
        <p class="text-muted">This will also remove the linked login account for {{ student.user.username }}.</p>
        <form method="post" class="d-flex gap-2">
            {% csrf_token %}
            <button type="submit" class="btn btn-danger rounded-pill">Delete Student</button>
            <a href="{% url 'students:detail' student.pk %}" class="btn btn-outline-secondary rounded-pill">Cancel</a>
        </form>
    </div>
{% endblock %}

```

## templates/teachers/teacher_list.html

```html
{% extends "base.html" %}

{% block title %}Teachers | {{ school_name }}{% endblock %}
{% block page_heading %}Teachers{% endblock %}

{% block content %}
    <div class="content-card">
        <div class="search-row">
            <form method="get" class="d-flex gap-2">
                <input type="text" name="q" value="{{ query }}" class="form-control" placeholder="Search by name, employee ID, or specialization">
                <button type="submit" class="btn btn-outline-success rounded-pill px-4">Search</button>
            </form>
            {% if current_role == 'admin' %}
                <a href="{% url 'teachers:add' %}" class="btn btn-brand">Add Teacher</a>
            {% endif %}
        </div>

        <div class="table-responsive">
            <table class="table align-middle app-table">
                <thead>
                    <tr>
                        <th>Employee ID</th>
                        <th>Teacher Name</th>
                        <th>Specialization</th>
                        <th>Email</th>
                        <th>Phone</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for teacher in teachers %}
                        <tr>
                            <td>{{ teacher.employee_id }}</td>
                            <td>{{ teacher.full_name }}</td>
                            <td>{{ teacher.specialization|default:"-" }}</td>
                            <td>{{ teacher.email|default:"-" }}</td>
                            <td>{{ teacher.phone|default:"-" }}</td>
                            <td class="d-flex gap-2 flex-wrap">
                                <a href="{% url 'teachers:detail' teacher.pk %}" class="btn btn-outline-success btn-sm rounded-pill">View</a>
                                {% if current_role == 'admin' %}
                                    <a href="{% url 'teachers:edit' teacher.pk %}" class="btn btn-outline-secondary btn-sm rounded-pill">Edit</a>
                                    <a href="{% url 'teachers:delete' teacher.pk %}" class="btn btn-outline-danger btn-sm rounded-pill">Delete</a>
                                {% endif %}
                            </td>
                        </tr>
                    {% empty %}
                        <tr>
                            <td colspan="6" class="text-center text-muted py-5">No teachers found.</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
{% endblock %}

```

## templates/teachers/teacher_detail.html

```html
{% extends "base.html" %}

{% block title %}Teacher Profile | {{ school_name }}{% endblock %}
{% block page_heading %}Teacher Profile{% endblock %}

{% block content %}
    <div class="content-card mb-4">
        <div class="section-title-wrap">
            <div>
                <h4 class="section-title">{{ teacher.full_name }}</h4>
                <p class="text-muted mb-0">Employee ID: {{ teacher.employee_id }}</p>
            </div>
            {% if current_role == 'admin' %}
                <div class="d-flex gap-2">
                    <a href="{% url 'teachers:edit' teacher.pk %}" class="btn btn-outline-secondary rounded-pill">Edit</a>
                    <a href="{% url 'teachers:delete' teacher.pk %}" class="btn btn-outline-danger rounded-pill">Delete</a>
                </div>
            {% endif %}
        </div>

        <div class="profile-layout">
            <div class="profile-photo-card">
                {% if teacher.user.profile.photo %}
                    <img src="{{ teacher.user.profile.photo.url }}" alt="{{ teacher.full_name }}" class="profile-photo">
                {% else %}
                    <div class="profile-photo profile-photo--placeholder">
                        <i class="bi bi-person-circle"></i>
                    </div>
                {% endif %}
            </div>
            <div class="profile-grid">
                <div class="profile-item"><span>Nationality</span><strong>{{ teacher.nationality|default:"-" }}</strong></div>
                <div class="profile-item"><span>Specialization</span><strong>{{ teacher.specialization|default:"-" }}</strong></div>
                <div class="profile-item"><span>Department</span><strong>{{ teacher.department|default:"-" }}</strong></div>
                <div class="profile-item"><span>Position</span><strong>{{ teacher.position|default:"-" }}</strong></div>
                <div class="profile-item"><span>Email</span><strong>{{ teacher.email|default:"-" }}</strong></div>
                <div class="profile-item"><span>Phone</span><strong>{{ teacher.phone|default:"-" }}</strong></div>
                <div class="profile-item"><span>Hired On</span><strong>{{ teacher.hired_on }}</strong></div>
                <div class="profile-item"><span>Username</span><strong>{{ teacher.user.username }}</strong></div>
            </div>
        </div>
    </div>

    <div class="content-card mb-4">
        <h4 class="section-title mb-3">Qualifications</h4>
        <p class="mb-0">{{ teacher.qualifications|default:"No qualifications added yet." }}</p>
    </div>

    <div class="content-card">
        <h4 class="section-title mb-3">Address</h4>
        <p class="mb-0">{{ teacher.address|default:"No address supplied yet." }}</p>
    </div>
{% endblock %}

```

## templates/teachers/teacher_form.html

```html
{% extends "base.html" %}

{% block title %}{{ page_title }} | {{ school_name }}{% endblock %}
{% block page_heading %}{{ page_title }}{% endblock %}

{% block content %}
    <div class="form-card">
        <form method="post" enctype="multipart/form-data">
            {% csrf_token %}
            <div class="row g-4">
                {% include "includes/form_fields.html" %}
            </div>
            <div class="d-flex gap-2 mt-4">
                <button type="submit" class="btn btn-brand">{{ submit_label }}</button>
                <a href="{% url 'teachers:list' %}" class="btn btn-outline-secondary rounded-pill">Cancel</a>
            </div>
        </form>
    </div>
{% endblock %}

```

## templates/teachers/teacher_confirm_delete.html

```html
{% extends "base.html" %}

{% block title %}Delete Teacher | {{ school_name }}{% endblock %}
{% block page_heading %}Delete Teacher{% endblock %}

{% block content %}
    <div class="form-card">
        <h4 class="section-title">Remove {{ teacher.full_name }}?</h4>
        <p class="text-muted">This also removes the linked login account for {{ teacher.user.username }}.</p>
        <form method="post" class="d-flex gap-2">
            {% csrf_token %}
            <button type="submit" class="btn btn-danger rounded-pill">Delete Teacher</button>
            <a href="{% url 'teachers:detail' teacher.pk %}" class="btn btn-outline-secondary rounded-pill">Cancel</a>
        </form>
    </div>
{% endblock %}

```

## templates/academics/class_list.html

```html
{% extends "base.html" %}

{% block title %}Classes | {{ school_name }}{% endblock %}
{% block page_heading %}Classes{% endblock %}

{% block content %}
    <div class="content-card">
        <div class="search-row">
            <form method="get" class="d-flex gap-2">
                <input type="text" name="q" value="{{ query }}" class="form-control" placeholder="Search by class name, section, or teacher">
                <button type="submit" class="btn btn-outline-success rounded-pill px-4">Search</button>
            </form>
            {% if current_role == 'admin' %}
                <a href="{% url 'academics:class_add' %}" class="btn btn-brand">Create Class</a>
            {% endif %}
        </div>

        <div class="table-responsive">
            <table class="table align-middle app-table">
                <thead>
                    <tr>
                        <th>Class</th>
                        <th>Section</th>
                        <th>Class Teacher</th>
                        <th>Description</th>
                        <th>Students</th>
                        {% if current_role == 'admin' %}<th>Actions</th>{% endif %}
                    </tr>
                </thead>
                <tbody>
                    {% for class_item in classes %}
                        <tr>
                            <td>{{ class_item.name }}</td>
                            <td>{{ class_item.section|default:"-" }}</td>
                            <td>{{ class_item.class_teacher.full_name|default:"Not Assigned" }}</td>
                            <td>{{ class_item.description|default:"-"|truncatechars:40 }}</td>
                            <td>{{ class_item.student_count }}</td>
                            {% if current_role == 'admin' %}
                                <td class="d-flex gap-2">
                                    <a href="{% url 'academics:class_edit' class_item.pk %}" class="btn btn-outline-secondary btn-sm rounded-pill">Edit</a>
                                    <a href="{% url 'academics:class_delete' class_item.pk %}" class="btn btn-outline-danger btn-sm rounded-pill">Delete</a>
                                </td>
                            {% endif %}
                        </tr>
                    {% empty %}
                        <tr><td colspan="6" class="text-center text-muted py-5">No classes created yet.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
{% endblock %}

```

## templates/academics/class_form.html

```html
{% extends "base.html" %}

{% block title %}{{ page_title }} | {{ school_name }}{% endblock %}
{% block page_heading %}{{ page_title }}{% endblock %}

{% block content %}
    <div class="form-card">
        <form method="post">
            {% csrf_token %}
            <div class="row g-4">
                {% include "includes/form_fields.html" %}
            </div>
            <div class="d-flex gap-2 mt-4">
                <button type="submit" class="btn btn-brand">{{ submit_label }}</button>
                <a href="{% url 'academics:class_list' %}" class="btn btn-outline-secondary rounded-pill">Cancel</a>
            </div>
        </form>
    </div>
{% endblock %}

```

## templates/academics/class_confirm_delete.html

```html
{% extends "base.html" %}

{% block title %}Delete Class | {{ school_name }}{% endblock %}
{% block page_heading %}Delete Class{% endblock %}

{% block content %}
    <div class="form-card">
        <h4 class="section-title">Delete {{ school_class }}?</h4>
        <p class="text-muted">Students linked to this class will lose the class assignment, and class-linked records will be removed.</p>
        <form method="post" class="d-flex gap-2">
            {% csrf_token %}
            <button type="submit" class="btn btn-danger rounded-pill">Delete Class</button>
            <a href="{% url 'academics:class_list' %}" class="btn btn-outline-secondary rounded-pill">Cancel</a>
        </form>
    </div>
{% endblock %}

```

## templates/academics/subject_list.html

```html
{% extends "base.html" %}

{% block title %}Subjects | {{ school_name }}{% endblock %}
{% block page_heading %}Subjects{% endblock %}

{% block content %}
    <div class="content-card">
        <div class="search-row">
            <form method="get" class="d-flex gap-2">
                <input type="text" name="q" value="{{ query }}" class="form-control" placeholder="Search by subject name or code">
                <button type="submit" class="btn btn-outline-success rounded-pill px-4">Search</button>
            </form>
            {% if current_role == 'admin' %}
                <a href="{% url 'academics:subject_add' %}" class="btn btn-brand">Create Subject</a>
            {% endif %}
        </div>

        <div class="table-responsive">
            <table class="table align-middle app-table">
                <thead>
                    <tr>
                        <th>Code</th>
                        <th>Name</th>
                        <th>Description</th>
                        {% if current_role == 'admin' %}<th>Actions</th>{% endif %}
                    </tr>
                </thead>
                <tbody>
                    {% for subject in subjects %}
                        <tr>
                            <td>{{ subject.code }}</td>
                            <td>{{ subject.name }}</td>
                            <td>{{ subject.description|default:"-"|truncatechars:50 }}</td>
                            {% if current_role == 'admin' %}
                                <td class="d-flex gap-2">
                                    <a href="{% url 'academics:subject_edit' subject.pk %}" class="btn btn-outline-secondary btn-sm rounded-pill">Edit</a>
                                    <a href="{% url 'academics:subject_delete' subject.pk %}" class="btn btn-outline-danger btn-sm rounded-pill">Delete</a>
                                </td>
                            {% endif %}
                        </tr>
                    {% empty %}
                        <tr><td colspan="4" class="text-center text-muted py-5">No subjects created yet.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
{% endblock %}

```

## templates/academics/subject_form.html

```html
{% extends "base.html" %}

{% block title %}{{ page_title }} | {{ school_name }}{% endblock %}
{% block page_heading %}{{ page_title }}{% endblock %}

{% block content %}
    <div class="form-card">
        <form method="post">
            {% csrf_token %}
            <div class="row g-4">
                {% include "includes/form_fields.html" %}
            </div>
            <div class="d-flex gap-2 mt-4">
                <button type="submit" class="btn btn-brand">{{ submit_label }}</button>
                <a href="{% url 'academics:subject_list' %}" class="btn btn-outline-secondary rounded-pill">Cancel</a>
            </div>
        </form>
    </div>
{% endblock %}

```

## templates/academics/subject_confirm_delete.html

```html
{% extends "base.html" %}

{% block title %}Delete Subject | {{ school_name }}{% endblock %}
{% block page_heading %}Delete Subject{% endblock %}

{% block content %}
    <div class="form-card">
        <h4 class="section-title">Delete {{ subject.name }}?</h4>
        <p class="text-muted">Any assignments and grades linked to this subject will also be affected.</p>
        <form method="post" class="d-flex gap-2">
            {% csrf_token %}
            <button type="submit" class="btn btn-danger rounded-pill">Delete Subject</button>
            <a href="{% url 'academics:subject_list' %}" class="btn btn-outline-secondary rounded-pill">Cancel</a>
        </form>
    </div>
{% endblock %}

```

## templates/academics/assignment_list.html

```html
{% extends "base.html" %}

{% block title %}Teaching Assignments | {{ school_name }}{% endblock %}
{% block page_heading %}Teacher Assignments{% endblock %}

{% block content %}
    <div class="content-card">
        <div class="section-title-wrap">
            <h4 class="section-title">Class and Subject Assignments</h4>
            {% if current_role == 'admin' or current_role == 'teacher' %}
                <a href="{% url 'academics:assignment_add' %}" class="btn btn-brand">Assign Teacher</a>
            {% endif %}
        </div>

        <div class="table-responsive">
            <table class="table align-middle app-table">
                <thead>
                    <tr>
                        <th>Teacher</th>
                        <th>Class</th>
                        <th>Subject</th>
                        <th>Created</th>
                        {% if current_role == 'admin' or current_role == 'teacher' %}<th>Actions</th>{% endif %}
                    </tr>
                </thead>
                <tbody>
                    {% for assignment in assignments %}
                        <tr>
                            <td>{{ assignment.teacher.full_name }}</td>
                            <td>{{ assignment.school_class }}</td>
                            <td>{{ assignment.subject.name }}</td>
                            <td>{{ assignment.created_at|date:"M d, Y" }}</td>
                            {% if current_role == 'admin' or current_role == 'teacher' %}
                                <td class="d-flex gap-2">
                                    <a href="{% url 'academics:assignment_edit' assignment.pk %}" class="btn btn-outline-secondary btn-sm rounded-pill">Edit</a>
                                    <a href="{% url 'academics:assignment_delete' assignment.pk %}" class="btn btn-outline-danger btn-sm rounded-pill">Delete</a>
                                </td>
                            {% endif %}
                        </tr>
                    {% empty %}
                        <tr><td colspan="{% if current_role == 'admin' or current_role == 'teacher' %}5{% else %}4{% endif %}" class="text-center text-muted py-5">No teacher assignments created yet.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
{% endblock %}

```

## templates/academics/assignment_form.html

```html
{% extends "base.html" %}

{% block title %}{{ page_title }} | {{ school_name }}{% endblock %}
{% block page_heading %}{{ page_title }}{% endblock %}

{% block content %}
    <div class="form-card">
        <form method="post">
            {% csrf_token %}
            <div class="row g-4">
                {% include "includes/form_fields.html" %}
            </div>
            <div class="d-flex gap-2 mt-4">
                <button type="submit" class="btn btn-brand">{{ submit_label }}</button>
                <a href="{% url 'academics:assignment_list' %}" class="btn btn-outline-secondary rounded-pill">Cancel</a>
            </div>
        </form>
    </div>
{% endblock %}

```

## templates/academics/assignment_confirm_delete.html

```html
{% extends "base.html" %}

{% block title %}Delete Assignment | {{ school_name }}{% endblock %}
{% block page_heading %}Delete Assignment{% endblock %}

{% block content %}
    <div class="form-card">
        <h4 class="section-title">Delete this assignment?</h4>
        <p class="text-muted">{{ assignment.teacher.full_name }} is currently assigned to {{ assignment.subject.name }} in {{ assignment.school_class }}.</p>
        <form method="post" class="d-flex gap-2">
            {% csrf_token %}
            <button type="submit" class="btn btn-danger rounded-pill">Delete Assignment</button>
            <a href="{% url 'academics:assignment_list' %}" class="btn btn-outline-secondary rounded-pill">Cancel</a>
        </form>
    </div>
{% endblock %}

```

## templates/academics/attendance_form.html

```html
{% extends "base.html" %}

{% block title %}Mark Attendance | {{ school_name }}{% endblock %}
{% block page_heading %}Mark Attendance{% endblock %}

{% block content %}
    <div class="content-card mb-4">
        <h4 class="section-title mb-3">Choose Class and Date</h4>
        <form method="get" class="row g-3 align-items-end">
            <div class="col-md-5">
                <label class="form-label fw-semibold">Class</label>
                {{ form.school_class }}
            </div>
            <div class="col-md-4">
                <label class="form-label fw-semibold">Date</label>
                {{ form.date }}
            </div>
            <div class="col-md-3">
                <button type="submit" class="btn btn-brand w-100">Load Students</button>
            </div>
        </form>
    </div>

    {% if attendance_rows %}
        <div class="content-card">
            <div class="section-title-wrap">
                <h4 class="section-title">{{ selected_class }} Attendance</h4>
                <span class="status-pill">{{ selected_date }}</span>
            </div>
            <form method="post">
                {% csrf_token %}
                <input type="hidden" name="school_class" value="{{ selected_class.pk }}">
                <input type="hidden" name="date" value="{{ selected_date|date:'Y-m-d' }}">
                <div class="table-responsive">
                    <table class="table align-middle app-table">
                        <thead>
                            <tr>
                                <th>Admission No.</th>
                                <th>Student</th>
                                <th>Status</th>
                                <th>Note</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for row in attendance_rows %}
                                <tr>
                                    <td>{{ row.student.admission_number }}</td>
                                    <td>{{ row.student.full_name }}</td>
                                    <td>
                                        <select name="status_{{ row.student.id }}" class="form-select table-input">
                                            <option value="Present" {% if row.status == 'Present' %}selected{% endif %}>Present</option>
                                            <option value="Absent" {% if row.status == 'Absent' %}selected{% endif %}>Absent</option>
                                            <option value="Late" {% if row.status == 'Late' %}selected{% endif %}>Late</option>
                                            <option value="Excused" {% if row.status == 'Excused' %}selected{% endif %}>Excused</option>
                                        </select>
                                    </td>
                                    <td>
                                        <input type="text" name="note_{{ row.student.id }}" class="form-control" value="{{ row.note }}" placeholder="Optional note">
                                    </td>
                                </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                <button type="submit" class="btn btn-brand mt-3">Save Attendance</button>
            </form>
        </div>
    {% endif %}
{% endblock %}

```

## templates/academics/attendance_list.html

```html
{% extends "base.html" %}

{% block title %}Attendance Records | {{ school_name }}{% endblock %}
{% block page_heading %}Attendance Records{% endblock %}

{% block content %}
    <div class="content-card mb-4">
        <h4 class="section-title mb-3">Filter Records</h4>
        <form method="get" class="row g-3 align-items-end">
            <div class="col-md-5">
                <label class="form-label fw-semibold">Class</label>
                {{ form.school_class }}
            </div>
            <div class="col-md-4">
                <label class="form-label fw-semibold">Date</label>
                {{ form.date }}
            </div>
            <div class="col-md-3">
                <button type="submit" class="btn btn-brand w-100">View Records</button>
            </div>
        </form>
    </div>

    <div class="content-card">
        <div class="table-responsive">
            <table class="table align-middle app-table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Class</th>
                        <th>Student</th>
                        <th>Status</th>
                        <th>Marked By</th>
                        <th>Note</th>
                    </tr>
                </thead>
                <tbody>
                    {% for record in records %}
                        <tr>
                            <td>{{ record.date }}</td>
                            <td>{{ record.school_class }}</td>
                            <td>{{ record.student.full_name }}</td>
                            <td><span class="status-pill">{{ record.status }}</span></td>
                            <td>{{ record.marked_by.full_name|default:"Admin" }}</td>
                            <td>{{ record.note|default:"-" }}</td>
                        </tr>
                    {% empty %}
                        <tr><td colspan="6" class="text-center text-muted py-5">Load a class and date to view attendance records.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
{% endblock %}

```

## templates/academics/grade_form.html

```html
{% extends "base.html" %}

{% block title %}Upload Grades | {{ school_name }}{% endblock %}
{% block page_heading %}Grade Upload{% endblock %}

{% block content %}
    <div class="content-card mb-4">
        <h4 class="section-title mb-3">Select Gradebook</h4>
        <form method="get" class="row g-3 align-items-end">
            <div class="col-md-4">
                <label class="form-label fw-semibold">Class</label>
                {{ form.school_class }}
            </div>
            <div class="col-md-4">
                <label class="form-label fw-semibold">Subject</label>
                {{ form.subject }}
            </div>
            <div class="col-md-2">
                <label class="form-label fw-semibold">Term</label>
                {{ form.term }}
            </div>
            <div class="col-md-2">
                <button type="submit" class="btn btn-brand w-100">Load</button>
            </div>
        </form>
    </div>

    {% if grade_rows %}
        <div class="content-card">
            <div class="section-title-wrap">
                <h4 class="section-title">{{ selected_subject.name }} - {{ selected_class }}</h4>
                <span class="status-pill">{{ selected_term }}</span>
            </div>
            <form method="post">
                {% csrf_token %}
                <input type="hidden" name="school_class" value="{{ selected_class.pk }}">
                <input type="hidden" name="subject" value="{{ selected_subject.pk }}">
                <input type="hidden" name="term" value="{{ selected_term }}">
                <div class="table-responsive">
                    <table class="table align-middle app-table">
                        <thead>
                            <tr>
                                <th>Student</th>
                                <th>CA Score /40</th>
                                <th>Exam Score /60</th>
                                <th>Remarks</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for row in grade_rows %}
                                <tr>
                                    <td>{{ row.student.full_name }}</td>
                                    <td><input type="number" step="0.01" min="0" max="40" name="ca_{{ row.student.id }}" class="form-control table-input" value="{{ row.ca_score }}"></td>
                                    <td><input type="number" step="0.01" min="0" max="60" name="exam_{{ row.student.id }}" class="form-control table-input" value="{{ row.exam_score }}"></td>
                                    <td><input type="text" name="remarks_{{ row.student.id }}" class="form-control" value="{{ row.remarks }}" placeholder="Optional comment"></td>
                                </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                <button type="submit" class="btn btn-brand mt-3">Save Grades</button>
            </form>
        </div>
    {% endif %}
{% endblock %}

```

## templates/academics/grade_list.html

```html
{% extends "base.html" %}

{% block title %}Results | {{ school_name }}{% endblock %}
{% block page_heading %}Results{% endblock %}

{% block content %}
    <div class="content-card mb-4">
        <div class="section-title-wrap">
            <h4 class="section-title">{% if current_role == 'student' %}My Results{% else %}Grade Records{% endif %}</h4>
        </div>
        <form method="get" class="row g-3 align-items-end">
            <div class="col-md-4">
                <label class="form-label fw-semibold">Term</label>
                <select name="term" class="form-select">
                    <option value="">All Terms</option>
                    {% for value, label in term_choices %}
                        <option value="{{ value }}" {% if term == value %}selected{% endif %}>{{ label }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="col-md-3">
                <button type="submit" class="btn btn-brand w-100">Filter</button>
            </div>
        </form>
    </div>

    <div class="content-card">
        <div class="table-responsive">
            <table class="table align-middle app-table">
                <thead>
                    <tr>
                        {% if current_role != 'student' %}<th>Student</th>{% endif %}
                        <th>Class</th>
                        <th>Subject</th>
                        <th>Term</th>
                        <th>CA</th>
                        <th>Exam</th>
                        <th>Total</th>
                        <th>Grade</th>
                        <th>Remarks</th>
                        {% if current_role != 'student' %}<th>Action</th>{% endif %}
                    </tr>
                </thead>
                <tbody>
                    {% for grade in grades %}
                        <tr>
                            {% if current_role != 'student' %}<td>{{ grade.student.full_name }}</td>{% endif %}
                            <td>{{ grade.school_class }}</td>
                            <td>{{ grade.subject.name }}</td>
                            <td>{{ grade.term }}</td>
                            <td>{{ grade.ca_score }}</td>
                            <td>{{ grade.exam_score }}</td>
                            <td>{{ grade.total_score|floatformat:2 }}</td>
                            <td><span class="status-pill">{{ grade.letter_grade }}</span></td>
                            <td>{{ grade.remarks|default:"-" }}</td>
                            {% if current_role != 'student' %}
                                <td><a href="{% url 'academics:grade_delete' grade.pk %}" class="btn btn-outline-danger btn-sm rounded-pill">Delete</a></td>
                            {% endif %}
                        </tr>
                    {% empty %}
                        <tr><td colspan="{% if current_role == 'student' %}8{% else %}10{% endif %}" class="text-center text-muted py-5">No grade records available.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
{% endblock %}

```

## templates/academics/grade_confirm_delete.html

```html
{% extends "base.html" %}

{% block title %}Delete Grade | {{ school_name }}{% endblock %}
{% block page_heading %}Delete Grade{% endblock %}

{% block content %}
    <div class="form-card">
        <h4 class="section-title">Delete this grade record?</h4>
        <p class="text-muted">{{ grade.student.full_name }} - {{ grade.subject.name }} - {{ grade.term }}</p>
        <form method="post" class="d-flex gap-2">
            {% csrf_token %}
            <button type="submit" class="btn btn-danger rounded-pill">Delete Grade</button>
            <a href="{% url 'academics:grade_list' %}" class="btn btn-outline-secondary rounded-pill">Cancel</a>
        </form>
    </div>
{% endblock %}

```

## static/css/style.css

```css
:root {
    --brand-green: #4f86f7;
    --brand-green-deep: #1f5fcc;
    --brand-ink: #1f2937;
    --brand-soft: #eef4fb;
    --brand-panel: #f8fbff;
    --brand-white: #ffffff;
    --brand-border: rgba(58, 84, 120, 0.14);
}

body {
    font-family: "Poppins", "Segoe UI", sans-serif;
    background: linear-gradient(180deg, #edf2f8 0%, #f8fbfe 100%);
    color: var(--brand-ink);
}

h1, h2, h3, h4, h5 {
    font-family: "Cormorant Garamond", Georgia, serif;
    letter-spacing: 0.02em;
}

.app-shell {
    position: relative;
    overflow-x: hidden;
}

.app-gradient {
    position: fixed;
    inset: 0;
    background:
        radial-gradient(circle at top left, rgba(79, 134, 247, 0.2), transparent 30%),
        radial-gradient(circle at bottom right, rgba(31, 95, 204, 0.12), transparent 28%);
    z-index: -1;
}

.sidebar-panel {
    min-height: 100vh;
    position: fixed;
    top: 0;
    left: 0;
    padding: 1.5rem;
}

.sidebar-panel__inner,
.sidebar-offcanvas {
    background: linear-gradient(180deg, #26354a 0%, #1c2634 100%);
    color: #dae6f5;
    border-right: 1px solid rgba(255, 255, 255, 0.06);
}

.brand-wrap {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 2rem;
}

.brand-mark {
    width: 3rem;
    height: 3rem;
    display: grid;
    place-items: center;
    border-radius: 1rem;
    background: linear-gradient(135deg, var(--brand-green), #8fb7ff);
    color: #ffffff;
    font-weight: 700;
    box-shadow: 0 18px 40px rgba(79, 134, 247, 0.28);
}

.brand-title {
    font-size: 1.8rem;
    margin: 0;
    color: #fff;
}

.brand-copy {
    color: rgba(218, 230, 245, 0.72);
    font-size: 0.9rem;
}

.sidebar-nav {
    gap: 0.45rem;
}

.sidebar-nav .nav-link {
    color: rgba(226, 236, 247, 0.88);
    border-radius: 1rem;
    padding: 0.9rem 1rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.sidebar-nav .nav-link:hover,
.sidebar-nav .nav-link:focus {
    background: rgba(79, 134, 247, 0.16);
    color: #fff;
}

.content-panel {
    padding: 1.5rem 1.2rem 2rem;
}

@media (min-width: 992px) {
    .content-panel {
        margin-left: 16.666667%;
        padding: 2rem;
    }
}

.content-topbar,
.mobile-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.topbar-actions {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    flex-wrap: wrap;
    justify-content: flex-end;
}

.page-heading {
    font-size: clamp(2rem, 2.6vw, 3rem);
}

.eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.16em;
    font-size: 0.78rem;
    color: var(--brand-green-deep);
    font-weight: 600;
}

.user-chip {
    display: flex;
    align-items: center;
    gap: 0.9rem;
    background: rgba(255, 255, 255, 0.85);
    border: 1px solid var(--brand-border);
    border-radius: 999px;
    padding: 0.6rem 0.8rem 0.6rem 1rem;
    box-shadow: 0 18px 40px rgba(24, 39, 63, 0.08);
}

.user-chip__meta {
    display: flex;
    flex-direction: column;
    line-height: 1.1;
}

.user-chip__name {
    font-weight: 600;
}

.user-chip__role {
    font-size: 0.8rem;
    color: #6b7a8e;
}

.user-chip__icon {
    font-size: 1.45rem;
    color: var(--brand-green-deep);
    width: 2.6rem;
    height: 2.6rem;
    display: grid;
    place-items: center;
    overflow: hidden;
    border-radius: 50%;
    background: rgba(79, 134, 247, 0.12);
}

.logout-btn {
    padding-inline: 1rem;
    white-space: nowrap;
}

.topbar-avatar {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.hero-card,
.content-card,
.form-card,
.stat-card {
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid var(--brand-border);
    border-radius: 1.6rem;
    box-shadow: 0 20px 40px rgba(27, 45, 68, 0.07);
}

.hero-card {
    padding: 1.75rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    background: linear-gradient(135deg, rgba(79, 134, 247, 0.16), rgba(255, 255, 255, 0.96));
}

.hero-card__title {
    font-size: 2.15rem;
    margin-bottom: 0.5rem;
}

.hero-card__text {
    max-width: 48rem;
    color: #58677c;
}

.hero-card__badge {
    width: 4.75rem;
    height: 4.75rem;
    display: grid;
    place-items: center;
    border-radius: 1.5rem;
    background: linear-gradient(135deg, var(--brand-green), var(--brand-green-deep));
    color: #fff;
    font-size: 1.7rem;
}

.stat-card {
    padding: 1.4rem;
}

.stat-card span {
    display: block;
    text-transform: uppercase;
    font-size: 0.78rem;
    letter-spacing: 0.12em;
    color: #6a7b93;
    margin-bottom: 0.5rem;
}

.stat-card strong {
    font-size: 2rem;
    color: var(--brand-ink);
}

.content-card,
.form-card {
    padding: 1.5rem;
}

.section-title-wrap {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
}

.section-title {
    margin: 0;
    font-size: 1.9rem;
}

.app-table thead th {
    font-size: 0.82rem;
    color: #70829a;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    border-bottom-width: 1px;
}

.app-table td,
.app-table th {
    padding-top: 0.95rem;
    padding-bottom: 0.95rem;
}

.btn-brand {
    background: linear-gradient(135deg, var(--brand-green), var(--brand-green-deep));
    border: none;
    color: #fff;
    border-radius: 999px;
    padding-inline: 1.15rem;
}

.btn-brand:hover,
.btn-brand:focus {
    color: #fff;
    opacity: 0.95;
}

.status-pill {
    display: inline-flex;
    align-items: center;
    padding: 0.4rem 0.8rem;
    border-radius: 999px;
    background: rgba(79, 134, 247, 0.14);
    color: var(--brand-green-deep);
    font-size: 0.85rem;
    font-weight: 600;
}

.search-row {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    justify-content: space-between;
    margin-bottom: 1rem;
}

.search-row form {
    flex: 1 1 20rem;
}

.mobile-header {
    padding: 1rem 1rem 0;
}

.mobile-school {
    text-align: right;
}

.mobile-school__title {
    display: block;
    font-weight: 700;
}

.mobile-school__subtitle {
    font-size: 0.85rem;
    color: #73859a;
}

.login-screen {
    min-height: 100vh;
    position: relative;
    background:
        linear-gradient(135deg, rgba(20, 36, 61, 0.45), rgba(18, 30, 46, 0.3)),
        url("../img/school-building-photo.png") center center / cover no-repeat;
    background-color: #1b283b;
    color: #fff;
}

.login-backdrop {
    position: absolute;
    inset: 0;
    background:
        linear-gradient(180deg, rgba(13, 22, 38, 0.12), rgba(13, 22, 38, 0.62)),
        radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.07), transparent 25%),
        radial-gradient(circle at 80% 30%, rgba(255, 255, 255, 0.05), transparent 22%);
    backdrop-filter: blur(2px);
}

.login-card {
    position: relative;
    z-index: 1;
}

.login-card {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    color: var(--brand-ink);
    border-radius: 2rem;
    padding: 2rem;
    box-shadow: 0 24px 60px rgba(18, 31, 52, 0.28);
}

.login-footer {
    margin-top: 1.4rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(32, 49, 43, 0.08);
    color: #5f6f84;
    font-size: 0.92rem;
}

.login-alt-actions {
    display: grid;
    gap: 0.75rem;
    margin-top: 1rem;
}

.registration-shell {
    min-height: 100vh;
    background: linear-gradient(180deg, #edf2f8 0%, #f8fbfe 100%);
    color: var(--brand-ink);
}

.registration-card {
    max-width: 1100px;
    margin: 0 auto;
    padding: 2rem;
    background: rgba(255, 255, 255, 0.96);
    border: 1px solid var(--brand-border);
    border-radius: 2rem;
    box-shadow: 0 24px 60px rgba(18, 31, 52, 0.12);
}

.registration-card--compact {
    max-width: 640px;
}

.registration-steps {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 0.9rem;
}

.registration-step {
    display: flex;
    align-items: center;
    gap: 0.9rem;
    padding: 1rem;
    border-radius: 1.2rem;
    background: var(--brand-panel);
    border: 1px solid var(--brand-border);
}

.registration-step--active {
    background: rgba(79, 134, 247, 0.12);
    border-color: rgba(79, 134, 247, 0.32);
}

.registration-step--complete {
    background: rgba(79, 134, 247, 0.08);
}

.registration-step__number {
    width: 2.2rem;
    height: 2.2rem;
    display: grid;
    place-items: center;
    border-radius: 50%;
    background: var(--brand-green-deep);
    color: #fff;
    font-weight: 700;
}

.registration-actions {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    margin-top: 1.5rem;
    flex-wrap: wrap;
}

.document-list {
    display: grid;
    gap: 0.8rem;
}

.document-link {
    display: inline-flex;
    align-items: center;
    gap: 0.6rem;
    width: fit-content;
    padding: 0.85rem 1rem;
    border-radius: 999px;
    background: rgba(79, 134, 247, 0.08);
    color: var(--brand-green-deep);
    text-decoration: none;
    font-weight: 600;
}

.document-link::before {
    content: "\f38b";
    font-family: "bootstrap-icons";
}

.profile-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 1rem;
}

.profile-layout {
    display: grid;
    grid-template-columns: minmax(180px, 220px) 1fr;
    gap: 1.5rem;
    align-items: start;
}

.profile-photo-card {
    padding: 1rem;
    border-radius: 1.4rem;
    background: var(--brand-panel);
    border: 1px solid var(--brand-border);
}

.profile-photo-card--wide {
    max-width: 320px;
}

.profile-photo {
    width: 100%;
    aspect-ratio: 1 / 1;
    object-fit: cover;
    border-radius: 1.2rem;
    display: block;
}

.profile-photo--placeholder {
    display: grid;
    place-items: center;
    background: linear-gradient(135deg, rgba(79, 134, 247, 0.14), rgba(31, 95, 204, 0.08));
    color: var(--brand-green-deep);
    font-size: 4.5rem;
}

.profile-item {
    padding: 1rem;
    border-radius: 1.2rem;
    background: var(--brand-panel);
    border: 1px solid var(--brand-border);
}

.profile-item span {
    display: block;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #72839a;
    margin-bottom: 0.35rem;
}

.profile-item strong {
    font-size: 1rem;
}

.form-card .form-control,
.form-card .form-select,
.login-card .form-control,
.content-card .form-control,
.content-card .form-select {
    border-radius: 1rem;
    border-color: rgba(48, 72, 106, 0.14);
    padding: 0.8rem 1rem;
}

.table-input {
    min-width: 7rem;
}

@media (max-width: 991.98px) {
    .hero-card {
        flex-direction: column;
        align-items: flex-start;
    }

    .content-topbar {
        align-items: flex-start;
        flex-direction: column;
    }

    .topbar-actions {
        width: 100%;
        justify-content: space-between;
    }

    .login-screen {
        background-position: 58% center;
    }

    .profile-layout {
        grid-template-columns: 1fr;
    }

    .registration-card {
        padding: 1.2rem;
    }
}

```

## README.md

```markdown
# Sim Tech Academy School Management System

This is a beginner-friendly Django school management system for **Sim Tech Academy**.

## Features

- Role-based login for Admin, Teacher, and Student users
- Student and staff self-registration with admin approval workflow
- Student management with create, update, delete, list, and profile pages
- Teacher management with create, update, delete, list, and profile pages
- Class and subject management
- Teacher-to-class and teacher-to-subject assignments
- Attendance marking per class and date
- Grade upload for teachers
- Result viewing for students
- Admin dashboard with simple statistics
- Responsive Bootstrap interface inspired by the provided screenshots

## Tech Stack

- Python
- Django
- SQLite
- Bootstrap 5

## Project Structure

- `simtech_academy/` - Django project settings and root URLs
- `accounts/` - login, logout, dashboard, role handling
- `students/` - student records and views
- `teachers/` - teacher records and views
- `academics/` - classes, subjects, assignments, attendance, grades
- `templates/` - shared and app templates
- `static/` - custom CSS

## How to Run

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Optional but recommended: set the Gmail app password for real email delivery:

Windows PowerShell:

```powershell
$env:SIMTECH_EMAIL_PASSWORD="your-gmail-app-password"
```

If this is not set, the system uses Django's console email backend for development.

3. Create migrations if needed:

```bash
python manage.py makemigrations
```

4. Apply migrations:

```bash
python manage.py migrate
```

5. Load sample data:

```bash
python manage.py seed_school
```

6. Start the development server:

```bash
python manage.py runserver
```

7. Open your browser:

```text
http://127.0.0.1:8000/
```

## Demo Logins

- Admin: `admin` / `admin12345`
- Teacher: `mchola` / `teacher12345`
- Student: `sianthony` / `student12345`

## Notes

- SQLite is used by default, so no extra database setup is required.
- Real email notifications are configured to use `tradersnestmedia@gmail.com`.
- SMS notifications use a console/logging fallback by default until a live Zambian SMS gateway is configured.
- Registration credentials are only generated and sent after admin approval.
- You can also create your own admin account with:

```bash
python manage.py createsuperuser
```

- A single-file code bundle is generated in `COMPLETE_PROJECT_CODE.md`.

```

## requirements.txt

```text
Django==6.0.3

```


