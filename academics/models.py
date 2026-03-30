from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q


def grade_level_choices():
    return [(grade, f"Grade {grade}") for grade in range(1, 13)]


class AcademicYear(models.Model):
    year = models.PositiveIntegerField(unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["-year"]

    def __str__(self):
        return str(self.year)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_current:
            AcademicYear.objects.exclude(pk=self.pk).filter(is_current=True).update(is_current=False)


class Term(models.Model):
    TERM_CHOICES = (
        (1, "Term 1"),
        (2, "Term 2"),
        (3, "Term 3"),
    )

    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="terms")
    term_number = models.PositiveSmallIntegerField(choices=TERM_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ["-academic_year__year", "term_number"]
        constraints = [
            models.UniqueConstraint(fields=["academic_year", "term_number"], name="unique_academic_year_term_number"),
        ]

    def __str__(self):
        return f"{self.academic_year} - {self.get_term_number_display()}"

    @property
    def label(self):
        return self.get_term_number_display()


class ExaminationType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    weight_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    applicable_from_grade = models.PositiveSmallIntegerField(choices=grade_level_choices(), null=True, blank=True)
    applicable_to_grade = models.PositiveSmallIntegerField(choices=grade_level_choices(), null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.weight_percentage}%)"


class GradingSystem(models.Model):
    grade_name = models.CharField(max_length=2)
    min_score = models.PositiveSmallIntegerField()
    max_score = models.PositiveSmallIntegerField()
    remark = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-max_score", "grade_name"]
        constraints = [
            models.UniqueConstraint(fields=["grade_name"], condition=Q(is_active=True), name="unique_active_grade_name"),
        ]

    def __str__(self):
        return f"{self.grade_name}: {self.min_score}-{self.max_score}"


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


class SubjectGradeLevel(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="grade_levels")
    grade_level = models.PositiveSmallIntegerField(choices=grade_level_choices())
    is_core = models.BooleanField(default=True)

    class Meta:
        ordering = ["grade_level", "subject__name"]
        constraints = [
            models.UniqueConstraint(fields=["subject", "grade_level"], name="unique_subject_grade_level"),
        ]

    def __str__(self):
        return f"{self.subject.name} - Grade {self.grade_level}"


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


class AttendanceRegister(models.Model):
    SAVE_MODE_AUTO = "auto"
    SAVE_MODE_MANUAL = "manual"

    SAVE_MODE_CHOICES = (
        (SAVE_MODE_AUTO, "Auto Save"),
        (SAVE_MODE_MANUAL, "Manual Save"),
    )

    date = models.DateField()
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="attendance_registers")
    saved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_registers",
    )
    save_mode = models.CharField(max_length=10, choices=SAVE_MODE_CHOICES, default=SAVE_MODE_MANUAL)
    total_students = models.PositiveIntegerField(default=0)
    present_count = models.PositiveIntegerField(default=0)
    absent_count = models.PositiveIntegerField(default=0)
    late_count = models.PositiveIntegerField(default=0)
    excused_count = models.PositiveIntegerField(default=0)
    pdf_snapshot = models.FileField(upload_to="attendance_registers/", blank=True, null=True)
    pdf_generated_at = models.DateTimeField(null=True, blank=True)
    last_saved_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "school_class__name", "school_class__section"]
        constraints = [
            models.UniqueConstraint(fields=["date", "school_class"], name="unique_daily_attendance_register"),
        ]

    def __str__(self):
        return f"{self.school_class} register - {self.date}"


class Grade(models.Model):
    TERM_CHOICES = (
        ("Term 1", "Term 1"),
        ("Term 2", "Term 2"),
        ("Term 3", "Term 3"),
    )

    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="grades")
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="grades")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="grades")
    term_record = models.ForeignKey(Term, on_delete=models.SET_NULL, null=True, blank=True, related_name="grades")
    examination_type = models.ForeignKey(
        ExaminationType,
        on_delete=models.PROTECT,
        related_name="grades",
        null=True,
        blank=True,
    )
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
            models.UniqueConstraint(
                fields=["student", "subject", "term", "examination_type"],
                name="unique_student_subject_term_exam_type_grade",
            ),
        ]

    def __str__(self):
        return f"{self.student.full_name} - {self.subject.name} - {self.term}"

    @property
    def total_score(self):
        return float(self.ca_score) + float(self.exam_score)

    @property
    def letter_grade(self):
        total = self.total_score
        configured_grade = GradingSystem.objects.filter(
            is_active=True,
            min_score__lte=total,
            max_score__gte=total,
        ).order_by("-max_score", "grade_name").first()
        if configured_grade:
            return configured_grade.grade_name
        if total >= 80:
            return "A"
        if total >= 70:
            return "B"
        if total >= 60:
            return "C"
        if total >= 50:
            return "D"
        return "F"

    @property
    def grade_remark(self):
        total = self.total_score
        configured_grade = GradingSystem.objects.filter(
            is_active=True,
            min_score__lte=total,
            max_score__gte=total,
        ).order_by("-max_score", "grade_name").first()
        if configured_grade:
            return configured_grade.remark
        return self.remarks or ""


class ClassNote(models.Model):
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="notes")
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True, related_name="notes")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    attachment = models.FileField(upload_to="class_notes/")
    uploaded_by = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_notes",
    )
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "school_class__name", "title"]

    def __str__(self):
        return f"{self.title} - {self.school_class}"

    @property
    def attachment_name(self):
        return self.attachment.name.rsplit("/", 1)[-1] if self.attachment else ""
