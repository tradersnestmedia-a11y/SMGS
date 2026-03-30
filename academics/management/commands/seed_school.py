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
