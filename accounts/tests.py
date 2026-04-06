from datetime import date
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from academics.models import SchoolClass
from students.models import Student

from .models import ParentProfile, StudentRegistration, UserProfile
from .services import approve_student_registration, create_parent_account


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="school@example.com",
    SERVER_EMAIL="school@example.com",
    SIMTECH_SMS_ALWAYS_SEND=False,
)
class StudentRegistrationApprovalTests(TestCase):
    def test_approval_creates_student_with_gender_address_and_sends_email(self):
        admin = User.objects.create_user(username="admin", password="testpass123")
        admin.profile.role = UserProfile.ROLE_ADMIN
        admin.profile.save()
        SchoolClass.objects.create(name="Grade 5")

        registration = StudentRegistration.objects.create(
            full_name="Jane Doe",
            nationality="Zambian",
            zambian_phone="0977000000",
            personal_email="jane@example.com",
            date_of_birth=date(2012, 1, 10),
            gender="Female",
            guardian_name="John Doe",
            guardian_relationship="Father",
            guardian_phone="0977111111",
            guardian_email="guardian@example.com",
            address="Kafue Road, Lusaka",
            previous_school_attended="Riverdale School",
            last_grade_attended="Grade 4",
            target_grade="Grade 5",
        )

        username, _ = approve_student_registration(registration, admin, "http://testserver/login/")

        student = Student.objects.get(admission_number=username)
        registration.refresh_from_db()

        self.assertEqual(student.gender, "Female")
        self.assertEqual(student.address, "Kafue Road, Lusaka")
        self.assertEqual(student.current_class.name, "Grade 5")
        self.assertEqual(registration.approved_user.username, username)
        self.assertTrue(registration.email_sent)

    def test_user_can_update_own_profile_photo(self):
        user = User.objects.create_user(username="photo_user", password="testpass123")
        temp_media_root = tempfile.mkdtemp()

        try:
            self.client.force_login(user)
            with self.settings(MEDIA_ROOT=temp_media_root):
                response = self.client.post(
                    reverse("accounts:profile"),
                    {
                        "first_name": "Photo",
                        "last_name": "User",
                        "email": "photo@example.com",
                        "phone": "0977999999",
                        "photo": SimpleUploadedFile("avatar.jpg", b"fake-image-content", content_type="image/jpeg"),
                    },
                    follow=True,
                )

                user.refresh_from_db()
                self.assertEqual(response.status_code, 200)
                self.assertEqual(user.first_name, "Photo")
                self.assertEqual(user.profile.phone, "0977999999")
                self.assertIn("avatar", user.profile.photo.name)
        finally:
            shutil.rmtree(temp_media_root, ignore_errors=True)

    def test_existing_parent_is_linked_on_student_approval(self):
        admin = User.objects.create_user(username="admin_link", password="testpass123")
        admin.profile.role = UserProfile.ROLE_ADMIN
        admin.profile.save()

        parent_user = User.objects.create_user(username="parent1", password="testpass123", email="guardian@example.com")
        parent_user.profile.role = UserProfile.ROLE_PARENT
        parent_user.profile.save()
        parent = ParentProfile.objects.create(
            user=parent_user,
            phone_number="0977111111",
            relationship="Mother",
        )
        SchoolClass.objects.create(name="Grade 5")

        registration = StudentRegistration.objects.create(
            full_name="Pendo Zulu",
            nationality="Zambian",
            zambian_phone="0977000001",
            personal_email="pendo@example.com",
            date_of_birth=date(2012, 6, 12),
            gender="Female",
            guardian_name="Mercy Zulu",
            guardian_relationship="Mother",
            guardian_phone="0977111111",
            guardian_email="guardian@example.com",
            address="Lusaka West",
            previous_school_attended="Hope School",
            last_grade_attended="Grade 4",
            target_grade="Grade 5",
        )

        username, _ = approve_student_registration(registration, admin, "http://testserver/login/")

        student = Student.objects.get(admission_number=username)
        self.assertTrue(parent.students.filter(pk=student.pk).exists())


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="school@example.com",
)
class ParentAccountCreationTests(TestCase):
    def test_create_parent_account_sends_credentials_email(self):
        admin = User.objects.create_user(username="admin_parent", password="testpass123")
        admin.profile.role = UserProfile.ROLE_ADMIN
        admin.profile.save()

        student_user = User.objects.create_user(username="stu-parent-link", password="testpass123")
        student = Student.objects.create(
            user=student_user,
            admission_number="STU-2026-4001",
            first_name="Luka",
            last_name="Banda",
            gender="Male",
            joined_on=date.today(),
        )

        parent, password, email_sent, _ = create_parent_account(
            {
                "username": "parent-portal",
                "first_name": "Agnes",
                "last_name": "Banda",
                "email": "agnes@example.com",
                "phone_number": "0977333333",
                "occupation": "Trader",
                "relationship": "Mother",
                "physical_address": "Kanyama, Lusaka",
                "district": "Lusaka",
                "province": "Lusaka",
                "students": [student],
                "photo": None,
            },
            admin,
            "http://testserver/login/",
        )

        self.assertTrue(email_sent)
        self.assertEqual(parent.user.profile.role, UserProfile.ROLE_PARENT)
        self.assertTrue(parent.students.filter(pk=student.pk).exists())
        self.assertTrue(password)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("parent-portal", mail.outbox[0].body)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend",
    DEFAULT_FROM_EMAIL="school@example.com",
)
class ConsoleEmailBehaviorTests(TestCase):
    def test_console_backend_does_not_mark_registration_email_as_sent(self):
        admin = User.objects.create_user(username="admin_console", password="testpass123")
        admin.profile.role = UserProfile.ROLE_ADMIN
        admin.profile.save()
        SchoolClass.objects.create(name="Grade 5")

        registration = StudentRegistration.objects.create(
            full_name="Console Case",
            nationality="Zambian",
            zambian_phone="0977000100",
            personal_email="console@example.com",
            date_of_birth=date(2013, 2, 1),
            gender="Male",
            guardian_name="Guardian Case",
            guardian_relationship="Father",
            guardian_phone="0977000200",
            guardian_email="guardian.console@example.com",
            address="Lusaka",
            previous_school_attended="Test School",
            last_grade_attended="Grade 4",
            target_grade="Grade 5",
        )

        approve_student_registration(registration, admin, "http://testserver/login/")
        registration.refresh_from_db()

        self.assertFalse(registration.email_sent)
        self.assertIn("Console email backend is active", registration.notification_summary)
