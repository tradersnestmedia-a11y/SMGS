from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q, Sum
from django.utils import timezone


def grade_level_choices():
    return [(grade, f"Grade {grade}") for grade in range(1, 13)]


def generate_receipt_number():
    year = timezone.now().year
    base = f"RCT-{year}-"
    latest_receipt = (
        FeePayment.objects.filter(receipt_number__startswith=base)
        .order_by("-receipt_number")
        .values_list("receipt_number", flat=True)
        .first()
    )
    next_number = int(latest_receipt.split("-")[-1]) + 1 if latest_receipt else 1
    return f"RCT-{year}-{next_number:05d}"


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


class FeeStructure(models.Model):
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="fee_structures")
    grade_level = models.PositiveSmallIntegerField(choices=grade_level_choices())
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    development_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    examination_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    activity_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-term__academic_year__year", "term__term_number", "grade_level"]
        constraints = [
            models.UniqueConstraint(fields=["term", "grade_level"], name="unique_term_grade_fee_structure"),
        ]

    def __str__(self):
        return f"{self.term} - Grade {self.grade_level}"

    @property
    def total_amount(self):
        return sum(
            (
                self.tuition_fee,
                self.development_fee,
                self.examination_fee,
                self.activity_fee,
            ),
            Decimal("0.00"),
        )


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


class FeePayment(models.Model):
    METHOD_CASH = "cash"
    METHOD_MOBILE_MONEY = "mobile_money"
    METHOD_BANK_TRANSFER = "bank_transfer"
    METHOD_POS = "pos"

    PAYMENT_METHOD_CHOICES = (
        (METHOD_CASH, "Cash"),
        (METHOD_MOBILE_MONEY, "Mobile Money"),
        (METHOD_BANK_TRANSFER, "Bank Transfer"),
        (METHOD_POS, "POS / Card"),
    )

    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="fee_payments")
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="fee_payments")
    fee_structure = models.ForeignKey(
        FeeStructure,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(default=timezone.localdate)
    receipt_number = models.CharField(max_length=30, unique=True, editable=False)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default=METHOD_CASH)
    transaction_reference = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_fee_payments",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-payment_date", "-created_at", "-id"]

    def __str__(self):
        return f"{self.receipt_number} - {self.student.full_name}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = generate_receipt_number()
        if not self.fee_structure_id:
            self.fee_structure = get_fee_structure_for_student(self.student, self.term)
        super().save(*args, **kwargs)

    @property
    def expected_amount(self):
        return self.fee_structure.total_amount if self.fee_structure else Decimal("0.00")


def get_current_term():
    today = timezone.localdate()
    current_term = (
        Term.objects.select_related("academic_year")
        .filter(academic_year__is_current=True, start_date__lte=today, end_date__gte=today)
        .order_by("term_number")
        .first()
    )
    if current_term:
        return current_term
    return (
        Term.objects.select_related("academic_year")
        .filter(academic_year__is_current=True)
        .order_by("term_number")
        .first()
        or Term.objects.select_related("academic_year").order_by("-academic_year__year", "-term_number").first()
    )


def get_fee_structure_for_student(student, term):
    if not student or not term:
        return None
    grade_level = getattr(student, "grade_level", None)
    if not grade_level:
        return None
    return FeeStructure.objects.filter(term=term, grade_level=grade_level).first()


def calculate_student_fee_summary(student, term):
    fee_structure = get_fee_structure_for_student(student, term)
    expected_amount = fee_structure.total_amount if fee_structure else Decimal("0.00")
    amount_paid = (
        FeePayment.objects.filter(student=student, term=term).aggregate(total_paid=Sum("amount_paid"))["total_paid"]
        or Decimal("0.00")
    )
    return {
        "term": term,
        "fee_structure": fee_structure,
        "expected_amount": expected_amount,
        "amount_paid": amount_paid,
        "balance": expected_amount - amount_paid,
    }
