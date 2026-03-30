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
    GENDER_CHOICES = (
        ("Male", "Male"),
        ("Female", "Female"),
        ("Not Specified", "Not Specified"),
    )

    student_id = models.CharField(max_length=20, unique=True, editable=False)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default="Not Specified")
    guardian_name = models.CharField(max_length=150)
    guardian_relationship = models.CharField(max_length=100)
    guardian_phone = models.CharField(max_length=20)
    guardian_email = models.EmailField()
    address = models.TextField(blank=True)
    previous_school_attended = models.CharField(max_length=200)
    last_grade_attended = models.CharField(max_length=50)
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
