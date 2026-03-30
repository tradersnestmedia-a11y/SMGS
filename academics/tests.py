from datetime import date

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from students.models import Student

from accounts.models import UserProfile
from .models import AcademicYear, AttendanceRegister, ClassNote, ExaminationType, Grade, GradingSystem, SchoolClass, Subject


class NoteAccessTests(TestCase):
    def setUp(self):
        self.grade_7 = SchoolClass.objects.create(name="Grade 7")
        self.grade_8 = SchoolClass.objects.create(name="Grade 8")

        self.student_user = User.objects.create_user(username="student1", password="testpass123")
        self.student_user.profile.role = UserProfile.ROLE_STUDENT
        self.student_user.profile.save()
        self.student = Student.objects.create(
            user=self.student_user,
            admission_number="STU-2026-0001",
            first_name="Ada",
            last_name="Mwanza",
            gender="Female",
            email="ada@example.com",
            current_class=self.grade_7,
            joined_on=date.today(),
        )

    def test_student_only_sees_published_notes_for_own_class(self):
        visible_file = SimpleUploadedFile("visible.pdf", b"visible note", content_type="application/pdf")
        hidden_file = SimpleUploadedFile("hidden.pdf", b"hidden note", content_type="application/pdf")
        draft_file = SimpleUploadedFile("draft.pdf", b"draft note", content_type="application/pdf")
        ClassNote.objects.create(school_class=self.grade_7, title="Visible Note", attachment=visible_file, is_published=True)
        ClassNote.objects.create(school_class=self.grade_8, title="Other Class Note", attachment=hidden_file, is_published=True)
        ClassNote.objects.create(school_class=self.grade_7, title="Draft Note", attachment=draft_file, is_published=False)

        self.client.force_login(self.student_user)
        response = self.client.get(reverse("academics:note_list"))

        self.assertContains(response, "Visible Note")
        self.assertNotContains(response, "Other Class Note")
        self.assertNotContains(response, "Draft Note")


class AttendanceAutosaveTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(username="admin1", password="testpass123")
        self.admin_user.profile.role = UserProfile.ROLE_ADMIN
        self.admin_user.profile.save()

        self.school_class = SchoolClass.objects.create(name="Grade 6")
        self.student_one_user = User.objects.create_user(username="stu1", password="testpass123")
        self.student_two_user = User.objects.create_user(username="stu2", password="testpass123")
        Student.objects.create(
            user=self.student_one_user,
            admission_number="STU-2026-1001",
            first_name="John",
            last_name="Zulu",
            gender="Male",
            current_class=self.school_class,
            joined_on=date.today(),
        )
        Student.objects.create(
            user=self.student_two_user,
            admission_number="STU-2026-1002",
            first_name="Mary",
            last_name="Phiri",
            gender="Female",
            current_class=self.school_class,
            joined_on=date.today(),
        )

    def test_attendance_autosave_creates_register_and_summary_counts(self):
        students = list(Student.objects.filter(current_class=self.school_class).order_by("first_name", "last_name"))
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("academics:attendance_autosave"),
            {
                "school_class": self.school_class.pk,
                "date": "2026-03-30",
                f"status_{students[0].id}": "Present",
                f"note_{students[0].id}": "",
                f"status_{students[1].id}": "Absent",
                f"note_{students[1].id}": "Sick leave",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["summary"]["present"], 1)
        self.assertEqual(response.json()["summary"]["absent"], 1)

        register = AttendanceRegister.objects.get(school_class=self.school_class, date=date(2026, 3, 30))
        self.assertEqual(register.save_mode, AttendanceRegister.SAVE_MODE_AUTO)
        self.assertEqual(register.total_students, 2)
        self.assertEqual(register.present_count, 1)
        self.assertEqual(register.absent_count, 1)


class AcademicConfigurationTests(TestCase):
    def test_setting_current_academic_year_turns_off_previous_current_year(self):
        first_year = AcademicYear.objects.create(
            year=2026,
            start_date=date(2026, 1, 10),
            end_date=date(2026, 12, 5),
            is_current=True,
        )
        second_year = AcademicYear.objects.create(
            year=2027,
            start_date=date(2027, 1, 10),
            end_date=date(2027, 12, 5),
            is_current=True,
        )

        first_year.refresh_from_db()
        second_year.refresh_from_db()

        self.assertFalse(first_year.is_current)
        self.assertTrue(second_year.is_current)

    def test_grade_uses_configured_grading_rules(self):
        school_class = SchoolClass.objects.create(name="Grade 9")
        subject = Subject.objects.create(code="MAT", name="Mathematics")
        exam_type = ExaminationType.objects.get(name="Mock Exam")
        student_user = User.objects.create_user(username="gradeuser", password="testpass123")
        student = Student.objects.create(
            user=student_user,
            admission_number="STU-2026-0101",
            first_name="James",
            last_name="Banda",
            gender="Male",
            current_class=school_class,
            joined_on=date.today(),
        )
        GradingSystem.objects.update_or_create(
            grade_name="A",
            defaults={"min_score": 80, "max_score": 100, "remark": "Excellent", "is_active": True},
        )
        GradingSystem.objects.update_or_create(
            grade_name="B",
            defaults={"min_score": 60, "max_score": 79, "remark": "Very Good", "is_active": True},
        )

        grade = Grade.objects.create(
            school_class=school_class,
            student=student,
            subject=subject,
            term="Term 1",
            examination_type=exam_type,
            ca_score=35,
            exam_score=30,
        )

        self.assertEqual(grade.total_score, 65.0)
        self.assertEqual(grade.letter_grade, "B")
        self.assertEqual(grade.grade_remark, "Very Good")
