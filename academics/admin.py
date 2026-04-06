from django.contrib import admin

from .models import (
    AcademicYear,
    AttendanceRecord,
    AttendanceRegister,
    ClassNote,
    ExaminationType,
    FeePayment,
    FeeStructure,
    Grade,
    GradingSystem,
    SchoolClass,
    Subject,
    SubjectGradeLevel,
    TeachingAssignment,
    Term,
)


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ("year", "start_date", "end_date", "is_current")
    list_filter = ("is_current",)


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ("academic_year", "term_number", "start_date", "end_date")
    list_filter = ("academic_year", "term_number")


@admin.register(ExaminationType)
class ExaminationTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "weight_percentage", "applicable_from_grade", "applicable_to_grade")
    search_fields = ("name",)


@admin.register(GradingSystem)
class GradingSystemAdmin(admin.ModelAdmin):
    list_display = ("grade_name", "min_score", "max_score", "remark", "is_active")
    list_filter = ("is_active",)


@admin.register(SubjectGradeLevel)
class SubjectGradeLevelAdmin(admin.ModelAdmin):
    list_display = ("subject", "grade_level", "is_core")
    list_filter = ("grade_level", "is_core")


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
    list_display = ("student", "subject", "term", "examination_type", "ca_score", "exam_score", "uploaded_at")
    list_filter = ("term", "examination_type", "subject", "school_class")
    search_fields = ("student__first_name", "student__last_name")


@admin.register(AttendanceRegister)
class AttendanceRegisterAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "school_class",
        "save_mode",
        "total_students",
        "present_count",
        "absent_count",
        "last_saved_at",
    )
    list_filter = ("date", "save_mode", "school_class")
    search_fields = ("school_class__name", "school_class__section", "saved_by__username")


@admin.register(ClassNote)
class ClassNoteAdmin(admin.ModelAdmin):
    list_display = ("title", "school_class", "subject", "uploaded_by", "is_published", "created_at")
    list_filter = ("school_class", "subject", "is_published", "created_at")
    search_fields = ("title", "description", "school_class__name", "subject__name")


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ("term", "grade_level", "tuition_fee", "development_fee", "examination_fee", "activity_fee")
    list_filter = ("term__academic_year", "term", "grade_level")


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ("receipt_number", "student", "term", "amount_paid", "payment_method", "payment_date", "recorded_by")
    list_filter = ("term__academic_year", "term", "payment_method", "payment_date")
    search_fields = ("receipt_number", "student__first_name", "student__last_name", "student__admission_number", "transaction_reference")
