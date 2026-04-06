from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from students.models import Student

from accounts.models import ParentProfile, UserProfile
from .models import (
    AcademicYear,
    AttendanceRegister,
    ClassNote,
    ExaminationType,
    FeePayment,
    FeeStructure,
    Grade,
    GradingSystem,
    SchoolClass,
    Subject,
    Term,
)


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


class ParentAcademicAccessTests(TestCase):
    def setUp(self):
        self.school_class = SchoolClass.objects.create(name="Grade 8")
        self.subject = Subject.objects.create(code="SCI", name="Science")
        self.exam_type = ExaminationType.objects.get(name="End of Term")

        self.parent_user = User.objects.create_user(username="parentgrade", password="testpass123")
        self.parent_user.profile.role = UserProfile.ROLE_PARENT
        self.parent_user.profile.save()
        self.parent = ParentProfile.objects.create(user=self.parent_user, phone_number="0977444444")

        linked_user = User.objects.create_user(username="linked-student", password="testpass123")
        other_user = User.objects.create_user(username="other-student", password="testpass123")
        self.linked_student = Student.objects.create(
            user=linked_user,
            admission_number="STU-2026-5001",
            first_name="Ruth",
            last_name="Tembo",
            gender="Female",
            current_class=self.school_class,
            joined_on=date.today(),
        )
        self.other_student = Student.objects.create(
            user=other_user,
            admission_number="STU-2026-5002",
            first_name="Paul",
            last_name="Phiri",
            gender="Male",
            current_class=self.school_class,
            joined_on=date.today(),
        )
        self.parent.students.add(self.linked_student)

        Grade.objects.create(
            school_class=self.school_class,
            student=self.linked_student,
            subject=self.subject,
            term="Term 1",
            examination_type=self.exam_type,
            ca_score=32,
            exam_score=25,
        )
        Grade.objects.create(
            school_class=self.school_class,
            student=self.other_student,
            subject=self.subject,
            term="Term 1",
            examination_type=self.exam_type,
            ca_score=28,
            exam_score=20,
        )

    def test_parent_only_sees_linked_student_grades(self):
        self.client.force_login(self.parent_user)
        response = self.client.get(reverse("academics:grade_list"))

        self.assertContains(response, "Ruth Tembo")
        self.assertNotContains(response, "Paul Phiri")
        self.assertNotContains(response, "Delete")


class FeeStatementTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(username="feeadmin", password="testpass123")
        self.admin_user.profile.role = UserProfile.ROLE_ADMIN
        self.admin_user.profile.save()

        self.parent_user = User.objects.create_user(username="feeparent", password="testpass123")
        self.parent_user.profile.role = UserProfile.ROLE_PARENT
        self.parent_user.profile.save()
        self.parent = ParentProfile.objects.create(user=self.parent_user, phone_number="0977555555")

        self.school_class = SchoolClass.objects.create(name="Grade 7")
        self.student_user = User.objects.create_user(username="feestudent", password="testpass123")
        self.student_user.profile.role = UserProfile.ROLE_STUDENT
        self.student_user.profile.save()
        self.student = Student.objects.create(
            user=self.student_user,
            admission_number="STU-2026-6001",
            first_name="Esther",
            last_name="Soko",
            gender="Female",
            current_class=self.school_class,
            joined_on=date.today(),
        )
        self.parent.students.add(self.student)

        academic_year = AcademicYear.objects.create(
            year=2026,
            start_date=date(2026, 1, 10),
            end_date=date(2026, 12, 5),
            is_current=True,
        )
        self.term = Term.objects.create(
            academic_year=academic_year,
            term_number=1,
            start_date=date(2026, 1, 10),
            end_date=date(2026, 4, 10),
        )
        self.fee_structure = FeeStructure.objects.create(
            term=self.term,
            grade_level=7,
            tuition_fee=Decimal("2500.00"),
            development_fee=Decimal("300.00"),
            examination_fee=Decimal("120.00"),
            activity_fee=Decimal("80.00"),
        )
        self.payment = FeePayment.objects.create(
            student=self.student,
            term=self.term,
            fee_structure=self.fee_structure,
            amount_paid=Decimal("1000.00"),
            payment_method=FeePayment.METHOD_MOBILE_MONEY,
            transaction_reference="MM-12345",
            recorded_by=self.admin_user,
        )

    def test_parent_can_open_fee_statement(self):
        self.client.force_login(self.parent_user)
        response = self.client.get(reverse("academics:fee_statement", kwargs={"student_pk": self.student.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Esther Soko")
        self.assertContains(response, "ZMW 2000.00")

    def test_receipt_pdf_downloads_for_parent(self):
        self.client.force_login(self.parent_user)
        response = self.client.get(reverse("academics:fee_receipt", kwargs={"pk": self.payment.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn(self.payment.receipt_number.lower(), response["Content-Disposition"])
