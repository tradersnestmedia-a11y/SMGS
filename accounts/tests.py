from datetime import date
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from academics.models import SchoolClass
from students.models import Student

from .models import StudentRegistration, UserProfile
from .services import approve_student_registration


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
