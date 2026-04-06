import logging
import secrets
import string

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from academics.models import SchoolClass
from students.models import Student
from teachers.models import Teacher

from .models import NotificationLog, ParentProfile, StaffRegistration, StudentRegistration, UserProfile

logger = logging.getLogger(__name__)


def using_console_email_backend():
    return settings.EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend"


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
        f"Dear {name},\n\n"
        f"Your registration has been approved by the school administration.\n"
        f"Username: {username}\n"
        f"Temporary Password: {password}\n"
        f"Login URL: {login_url}\n\n"
        "Please sign in and change your password immediately after your first login."
    )


def send_user_credentials_email(name, recipient_email, username, password, login_url, subject):
    if not recipient_email:
        return False, "No recipient email supplied."
    if using_console_email_backend():
        return False, "Console email backend is active. Add SMTP credentials in .env to send real emails."

    message = build_credential_message(name, username, password, login_url)
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        return True, "Email sent successfully."
    except Exception as exc:  # pragma: no cover - external delivery failure
        return False, str(exc)


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
    if using_console_email_backend():
        response_message = "Console email backend is active. Add SMTP credentials in .env to send real emails."
        log_notification(
            registration,
            NotificationLog.CHANNEL_EMAIL,
            NotificationLog.STATUS_SKIPPED,
            recipient_email,
            subject,
            message,
            response_message,
        )
        return False, response_message

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


def link_student_to_matching_parents(student, registration):
    search_query = Q()
    if registration.guardian_email:
        search_query |= Q(user__email__iexact=registration.guardian_email)
    if registration.guardian_phone:
        search_query |= Q(phone_number=registration.guardian_phone)
    if not search_query:
        return

    for parent in ParentProfile.objects.filter(search_query).distinct():
        parent.students.add(student)


@transaction.atomic
def create_parent_account(cleaned_data, created_by, login_url):
    password = generate_secure_password()
    user = User.objects.create_user(
        username=cleaned_data["username"],
        password=password,
        first_name=cleaned_data["first_name"],
        last_name=cleaned_data["last_name"],
        email=cleaned_data["email"],
        is_active=True,
    )
    user.profile.role = UserProfile.ROLE_PARENT
    user.profile.phone = cleaned_data["phone_number"]
    if cleaned_data.get("photo"):
        user.profile.photo = cleaned_data["photo"]
    user.profile.save()

    parent = ParentProfile.objects.create(
        user=user,
        phone_number=cleaned_data["phone_number"],
        occupation=cleaned_data.get("occupation", ""),
        relationship=cleaned_data.get("relationship", ""),
        physical_address=cleaned_data.get("physical_address", ""),
        district=cleaned_data.get("district", ""),
        province=cleaned_data.get("province", ""),
    )
    parent.students.set(cleaned_data.get("students", []))

    subject = f"{settings.SCHOOL_NAME}: Parent Portal Access"
    email_sent, response_message = send_user_credentials_email(
        parent.full_name,
        user.email,
        user.username,
        password,
        login_url,
        subject,
    )
    logger.info(
        "Parent account %s created by %s. Email sent: %s (%s)",
        user.username,
        created_by.username,
        email_sent,
        response_message,
    )
    return parent, password, email_sent, response_message


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

    student = Student.objects.create(
        user=user,
        admission_number=username,
        first_name=first_name,
        last_name=last_name or first_name,
        gender=registration.gender,
        date_of_birth=registration.date_of_birth,
        nationality=registration.nationality,
        email=registration.personal_email,
        phone=registration.zambian_phone,
        guardian_name=registration.guardian_name,
        guardian_relationship=registration.guardian_relationship,
        guardian_phone=registration.guardian_phone,
        guardian_email=registration.guardian_email,
        address=registration.address,
        current_class=get_matching_class(registration.target_grade),
        joined_on=timezone.localdate(),
    )
    link_student_to_matching_parents(student, registration)

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
