from collections import Counter
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from accounts.models import UserProfile
from accounts.permissions import get_user_role, parent_can_access_student, role_required
from students.models import Student

from .forms import (
    AcademicYearForm,
    AttendanceSelectionForm,
    ClassNoteForm,
    ExaminationTypeForm,
    FeePaymentForm,
    FeeStructureForm,
    GradeUploadForm,
    GradingSystemForm,
    SchoolClassForm,
    SubjectForm,
    SubjectGradeLevelForm,
    TeachingAssignmentForm,
    TermForm,
)
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
    calculate_student_fee_summary,
    get_current_term,
)
from .pdf_utils import build_simple_text_pdf


def safe_decimal(value, upper_limit):
    try:
        decimal_value = Decimal(str(value or "0"))
    except InvalidOperation:
        decimal_value = Decimal("0")
    return max(Decimal("0"), min(Decimal(str(upper_limit)), decimal_value))


def teacher_can_access_class(user, school_class):
    teacher = getattr(user, "teacher_profile", None)
    if not teacher:
        return False
    return school_class.class_teacher_id == teacher.id or TeachingAssignment.objects.filter(
        teacher=teacher,
        school_class=school_class,
    ).exists()


def teacher_can_upload_subject_grade(user, school_class, subject):
    teacher = getattr(user, "teacher_profile", None)
    if not teacher:
        return False
    return TeachingAssignment.objects.filter(teacher=teacher, school_class=school_class, subject=subject).exists()


def get_teacher_accessible_classes(user):
    teacher = getattr(user, "teacher_profile", None)
    if not teacher:
        return SchoolClass.objects.none()
    return SchoolClass.objects.filter(
        Q(class_teacher=teacher) | Q(teaching_assignments__teacher=teacher)
    ).distinct()


def configure_assignment_form_for_user(request, form):
    if get_user_role(request.user) == UserProfile.ROLE_TEACHER:
        teacher = getattr(request.user, "teacher_profile", None)
        if not teacher:
            raise PermissionDenied
        form.fields["teacher"].queryset = form.fields["teacher"].queryset.filter(pk=teacher.pk)
        form.fields["teacher"].initial = teacher
        form.fields["teacher"].help_text = "Teachers can only create and manage their own assignments."
    return form


def configure_note_form_for_user(request, form):
    if get_user_role(request.user) == UserProfile.ROLE_TEACHER:
        form.fields["school_class"].queryset = get_teacher_accessible_classes(request.user)
        form.fields["school_class"].help_text = "You can upload notes only for classes assigned to you."
    return form


def save_model_form(request, form, success_message, redirect_name):
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, success_message)
        return redirect(redirect_name)
    return None


def user_can_access_student_finance(user, student):
    role = get_user_role(user)
    if role == UserProfile.ROLE_ADMIN:
        return True
    if role == UserProfile.ROLE_STUDENT:
        return getattr(user, "student_profile", None) == student
    if role == UserProfile.ROLE_PARENT:
        return parent_can_access_student(user, student)
    return False


def build_fee_receipt_lines(payment):
    summary = calculate_student_fee_summary(payment.student, payment.term)
    student = payment.student
    recorded_by = payment.recorded_by.get_full_name() if payment.recorded_by else "System"
    return [
        f"Receipt Number: {payment.receipt_number}",
        f"Payment Date: {payment.payment_date}",
        f"Student: {student.full_name}",
        f"Admission Number: {student.admission_number}",
        f"Class: {student.current_class or 'Not Assigned'}",
        f"Academic Term: {payment.term}",
        f"Payment Method: {payment.get_payment_method_display()}",
        f"Transaction Reference: {payment.transaction_reference or '-'}",
        f"Amount Paid: ZMW {payment.amount_paid:.2f}",
        f"Expected Fee: ZMW {summary['expected_amount']:.2f}",
        f"Total Paid To Date: ZMW {summary['amount_paid']:.2f}",
        f"Balance After Payment: ZMW {summary['balance']:.2f}",
        f"Recorded By: {recorded_by}",
        f"Notes: {payment.notes or '-'}",
    ]


def build_attendance_rows(selected_class, selected_date):
    students = Student.objects.filter(current_class=selected_class).order_by("first_name", "last_name")
    existing_records = {
        record.student_id: record
        for record in AttendanceRecord.objects.filter(school_class=selected_class, date=selected_date)
    }
    return [
        {
            "student": student,
            "status": existing_records.get(student.id).status if student.id in existing_records else AttendanceRecord.STATUS_PRESENT,
            "note": existing_records.get(student.id).note if student.id in existing_records else "",
        }
        for student in students
    ]


def summarize_attendance_statuses(statuses):
    counts = Counter(statuses)
    return {
        "total": sum(counts.values()),
        "present": counts.get(AttendanceRecord.STATUS_PRESENT, 0),
        "absent": counts.get(AttendanceRecord.STATUS_ABSENT, 0),
        "late": counts.get(AttendanceRecord.STATUS_LATE, 0),
        "excused": counts.get(AttendanceRecord.STATUS_EXCUSED, 0),
    }


def summarize_attendance_rows(attendance_rows):
    return summarize_attendance_statuses(row["status"] for row in attendance_rows)


def summarize_attendance_records(records):
    return summarize_attendance_statuses(record.status for record in records)


def persist_attendance_entries(selected_class, selected_date, user, post_data, save_mode):
    valid_statuses = {choice[0] for choice in AttendanceRecord.STATUS_CHOICES}
    teacher = getattr(user, "teacher_profile", None)
    attendance_rows = build_attendance_rows(selected_class, selected_date)
    saved_statuses = []

    for row in attendance_rows:
        student = row["student"]
        status = post_data.get(f"status_{student.id}", AttendanceRecord.STATUS_PRESENT)
        if status not in valid_statuses:
            status = AttendanceRecord.STATUS_PRESENT
        note = (post_data.get(f"note_{student.id}", "") or "").strip()
        AttendanceRecord.objects.update_or_create(
            date=selected_date,
            school_class=selected_class,
            student=student,
            defaults={"status": status, "note": note, "marked_by": teacher},
        )
        saved_statuses.append(status)

    summary = summarize_attendance_statuses(saved_statuses)
    register, _ = AttendanceRegister.objects.update_or_create(
        date=selected_date,
        school_class=selected_class,
        defaults={
            "saved_by": user,
            "save_mode": save_mode,
            "total_students": summary["total"],
            "present_count": summary["present"],
            "absent_count": summary["absent"],
            "late_count": summary["late"],
            "excused_count": summary["excused"],
        },
    )
    return register, summary


def build_attendance_pdf(selected_class, selected_date, records, attendance_register):
    saved_at = (
        timezone.localtime(attendance_register.last_saved_at).strftime("%Y-%m-%d %H:%M")
        if attendance_register
        else "Not recorded"
    )
    save_mode = attendance_register.get_save_mode_display() if attendance_register else "Manual Save"
    summary = (
        {
            "total": attendance_register.total_students,
            "present": attendance_register.present_count,
            "absent": attendance_register.absent_count,
            "late": attendance_register.late_count,
            "excused": attendance_register.excused_count,
        }
        if attendance_register
        else summarize_attendance_records(records)
    )
    lines = [
        f"School: {settings.SCHOOL_NAME}",
        f"Class: {selected_class}",
        f"Date: {selected_date.isoformat()}",
        f"Last Saved: {saved_at}",
        f"Save Mode: {save_mode}",
        (
            "Summary: "
            f"Total {summary['total']} | Present {summary['present']} | Absent {summary['absent']} | "
            f"Late {summary['late']} | Excused {summary['excused']}"
        ),
        "",
        "Admission No.  Student Name                    Status     Note",
        "--------------------------------------------------------------------------",
    ]
    for record in records:
        name = record.student.full_name[:30]
        note = record.note[:36]
        lines.append(
            f"{record.student.admission_number[:13]:<13}  {name:<30}  {record.status:<9}  {note}"
        )
    if not records:
        lines.append("No attendance entries were found for this register.")
    return build_simple_text_pdf(f"{settings.SCHOOL_NAME} Attendance Register", lines)


def build_attendance_pdf_response(selected_class, selected_date, attendance_register):
    records = list(
        AttendanceRecord.objects.select_related("student", "school_class", "marked_by")
        .filter(school_class=selected_class, date=selected_date)
        .order_by("student__first_name", "student__last_name")
    )
    pdf_bytes = build_attendance_pdf(selected_class, selected_date, records, attendance_register)
    filename = f"attendance-register-{slugify(str(selected_class))}-{selected_date.isoformat()}.pdf"
    attendance_register.pdf_snapshot.save(filename, ContentFile(pdf_bytes), save=False)
    attendance_register.pdf_generated_at = timezone.now()
    attendance_register.save(update_fields=["pdf_snapshot", "pdf_generated_at"])
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def class_list_view(request):
    query = request.GET.get("q", "").strip()
    classes = SchoolClass.objects.select_related("class_teacher")
    if query:
        classes = classes.filter(
            Q(name__icontains=query)
            | Q(section__icontains=query)
            | Q(class_teacher__first_name__icontains=query)
            | Q(class_teacher__last_name__icontains=query)
        )
    return render(request, "academics/class_list.html", {"classes": classes, "query": query})


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def class_create_view(request):
    form = SchoolClassForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Class created successfully.")
        return redirect("academics:class_list")
    return render(
        request,
        "academics/class_form.html",
        {"form": form, "page_title": "Create Class", "submit_label": "Save Class"},
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def class_update_view(request, pk):
    school_class = get_object_or_404(SchoolClass, pk=pk)
    form = SchoolClassForm(request.POST or None, instance=school_class)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Class updated successfully.")
        return redirect("academics:class_list")
    return render(
        request,
        "academics/class_form.html",
        {"form": form, "page_title": "Update Class", "submit_label": "Update Class"},
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def class_delete_view(request, pk):
    school_class = get_object_or_404(SchoolClass, pk=pk)
    if request.method == "POST":
        school_class.delete()
        messages.success(request, "Class deleted successfully.")
        return redirect("academics:class_list")
    return render(request, "academics/class_confirm_delete.html", {"school_class": school_class})


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def subject_list_view(request):
    query = request.GET.get("q", "").strip()
    subjects = Subject.objects.all()
    if query:
        subjects = subjects.filter(Q(name__icontains=query) | Q(code__icontains=query))
    return render(request, "academics/subject_list.html", {"subjects": subjects, "query": query})


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def subject_create_view(request):
    form = SubjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Subject created successfully.")
        return redirect("academics:subject_list")
    return render(
        request,
        "academics/subject_form.html",
        {"form": form, "page_title": "Create Subject", "submit_label": "Save Subject"},
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def subject_update_view(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    form = SubjectForm(request.POST or None, instance=subject)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Subject updated successfully.")
        return redirect("academics:subject_list")
    return render(
        request,
        "academics/subject_form.html",
        {"form": form, "page_title": "Update Subject", "submit_label": "Update Subject"},
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def subject_delete_view(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == "POST":
        subject.delete()
        messages.success(request, "Subject deleted successfully.")
        return redirect("academics:subject_list")
    return render(request, "academics/subject_confirm_delete.html", {"subject": subject})


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def calendar_overview_view(request):
    academic_years = AcademicYear.objects.prefetch_related("terms")
    terms = Term.objects.select_related("academic_year")
    return render(
        request,
        "academics/calendar_overview.html",
        {
            "academic_years": academic_years,
            "terms": terms,
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def academic_year_create_view(request):
    form = AcademicYearForm(request.POST or None)
    redirect_response = save_model_form(request, form, "Academic year created successfully.", "academics:calendar")
    if redirect_response:
        return redirect_response
    return render(
        request,
        "academics/config_form.html",
        {
            "form": form,
            "page_title": "Create Academic Year",
            "submit_label": "Save Academic Year",
            "cancel_url": reverse("academics:calendar"),
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def academic_year_update_view(request, pk):
    academic_year = get_object_or_404(AcademicYear, pk=pk)
    form = AcademicYearForm(request.POST or None, instance=academic_year)
    redirect_response = save_model_form(request, form, "Academic year updated successfully.", "academics:calendar")
    if redirect_response:
        return redirect_response
    return render(
        request,
        "academics/config_form.html",
        {
            "form": form,
            "page_title": "Update Academic Year",
            "submit_label": "Update Academic Year",
            "cancel_url": reverse("academics:calendar"),
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def academic_year_delete_view(request, pk):
    academic_year = get_object_or_404(AcademicYear, pk=pk)
    if request.method == "POST":
        academic_year.delete()
        messages.success(request, "Academic year deleted successfully.")
        return redirect("academics:calendar")
    return render(
        request,
        "academics/config_confirm_delete.html",
        {
            "item_label": str(academic_year),
            "item_type": "academic year",
            "cancel_url": reverse("academics:calendar"),
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def term_create_view(request):
    form = TermForm(request.POST or None)
    redirect_response = save_model_form(request, form, "Academic term created successfully.", "academics:calendar")
    if redirect_response:
        return redirect_response
    return render(
        request,
        "academics/config_form.html",
        {
            "form": form,
            "page_title": "Create Term",
            "submit_label": "Save Term",
            "cancel_url": reverse("academics:calendar"),
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def term_update_view(request, pk):
    term = get_object_or_404(Term, pk=pk)
    form = TermForm(request.POST or None, instance=term)
    redirect_response = save_model_form(request, form, "Academic term updated successfully.", "academics:calendar")
    if redirect_response:
        return redirect_response
    return render(
        request,
        "academics/config_form.html",
        {
            "form": form,
            "page_title": "Update Term",
            "submit_label": "Update Term",
            "cancel_url": reverse("academics:calendar"),
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def term_delete_view(request, pk):
    term = get_object_or_404(Term, pk=pk)
    if request.method == "POST":
        term.delete()
        messages.success(request, "Academic term deleted successfully.")
        return redirect("academics:calendar")
    return render(
        request,
        "academics/config_confirm_delete.html",
        {
            "item_label": str(term),
            "item_type": "term",
            "cancel_url": reverse("academics:calendar"),
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def grading_setup_view(request):
    exam_types = ExaminationType.objects.all()
    grading_rules = GradingSystem.objects.all()
    subject_grade_levels = SubjectGradeLevel.objects.select_related("subject")
    return render(
        request,
        "academics/grading_setup.html",
        {
            "exam_types": exam_types,
            "grading_rules": grading_rules,
            "subject_grade_levels": subject_grade_levels,
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def exam_type_create_view(request):
    form = ExaminationTypeForm(request.POST or None)
    redirect_response = save_model_form(request, form, "Examination type created successfully.", "academics:grading_setup")
    if redirect_response:
        return redirect_response
    return render(
        request,
        "academics/config_form.html",
        {
            "form": form,
            "page_title": "Create Examination Type",
            "submit_label": "Save Examination Type",
            "cancel_url": reverse("academics:grading_setup"),
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def exam_type_update_view(request, pk):
    exam_type = get_object_or_404(ExaminationType, pk=pk)
    form = ExaminationTypeForm(request.POST or None, instance=exam_type)
    redirect_response = save_model_form(request, form, "Examination type updated successfully.", "academics:grading_setup")
    if redirect_response:
        return redirect_response
    return render(
        request,
        "academics/config_form.html",
        {
            "form": form,
            "page_title": "Update Examination Type",
            "submit_label": "Update Examination Type",
            "cancel_url": reverse("academics:grading_setup"),
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def exam_type_delete_view(request, pk):
    exam_type = get_object_or_404(ExaminationType, pk=pk)
    if request.method == "POST":
        exam_type.delete()
        messages.success(request, "Examination type deleted successfully.")
        return redirect("academics:grading_setup")
    return render(
        request,
        "academics/config_confirm_delete.html",
        {
            "item_label": exam_type.name,
            "item_type": "examination type",
            "cancel_url": reverse("academics:grading_setup"),
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def grading_rule_create_view(request):
    form = GradingSystemForm(request.POST or None)
    redirect_response = save_model_form(request, form, "Grading rule created successfully.", "academics:grading_setup")
    if redirect_response:
        return redirect_response
    return render(
        request,
        "academics/config_form.html",
        {
            "form": form,
            "page_title": "Create Grading Rule",
            "submit_label": "Save Grading Rule",
            "cancel_url": reverse("academics:grading_setup"),
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def grading_rule_update_view(request, pk):
    grading_rule = get_object_or_404(GradingSystem, pk=pk)
    form = GradingSystemForm(request.POST or None, instance=grading_rule)
    redirect_response = save_model_form(request, form, "Grading rule updated successfully.", "academics:grading_setup")
    if redirect_response:
        return redirect_response
    return render(
        request,
        "academics/config_form.html",
        {
            "form": form,
            "page_title": "Update Grading Rule",
            "submit_label": "Update Grading Rule",
            "cancel_url": reverse("academics:grading_setup"),
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def grading_rule_delete_view(request, pk):
    grading_rule = get_object_or_404(GradingSystem, pk=pk)
    if request.method == "POST":
        grading_rule.delete()
        messages.success(request, "Grading rule deleted successfully.")
        return redirect("academics:grading_setup")
    return render(
        request,
        "academics/config_confirm_delete.html",
        {
            "item_label": str(grading_rule),
            "item_type": "grading rule",
            "cancel_url": reverse("academics:grading_setup"),
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def subject_grade_level_create_view(request):
    form = SubjectGradeLevelForm(request.POST or None)
    redirect_response = save_model_form(request, form, "Subject grade mapping created successfully.", "academics:grading_setup")
    if redirect_response:
        return redirect_response
    return render(
        request,
        "academics/config_form.html",
        {
            "form": form,
            "page_title": "Create Subject Grade Mapping",
            "submit_label": "Save Mapping",
            "cancel_url": reverse("academics:grading_setup"),
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def subject_grade_level_update_view(request, pk):
    subject_grade_level = get_object_or_404(SubjectGradeLevel, pk=pk)
    form = SubjectGradeLevelForm(request.POST or None, instance=subject_grade_level)
    redirect_response = save_model_form(request, form, "Subject grade mapping updated successfully.", "academics:grading_setup")
    if redirect_response:
        return redirect_response
    return render(
        request,
        "academics/config_form.html",
        {
            "form": form,
            "page_title": "Update Subject Grade Mapping",
            "submit_label": "Update Mapping",
            "cancel_url": reverse("academics:grading_setup"),
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def subject_grade_level_delete_view(request, pk):
    subject_grade_level = get_object_or_404(SubjectGradeLevel.objects.select_related("subject"), pk=pk)
    if request.method == "POST":
        subject_grade_level.delete()
        messages.success(request, "Subject grade mapping deleted successfully.")
        return redirect("academics:grading_setup")
    return render(
        request,
        "academics/config_confirm_delete.html",
        {
            "item_label": str(subject_grade_level),
            "item_type": "subject grade mapping",
            "cancel_url": reverse("academics:grading_setup"),
        },
    )


@login_required
def fee_statement_view(request, student_pk):
    student = get_object_or_404(Student.objects.select_related("current_class", "user"), pk=student_pk)
    if not user_can_access_student_finance(request.user, student):
        raise PermissionDenied

    term_ids = set(
        FeePayment.objects.filter(student=student).values_list("term_id", flat=True)
    )
    if student.grade_level:
        term_ids.update(
            Term.objects.filter(fee_structures__grade_level=student.grade_level).values_list("id", flat=True)
        )
    terms = Term.objects.select_related("academic_year").filter(pk__in=term_ids).order_by("-academic_year__year", "-term_number")
    if not term_ids and get_current_term():
        terms = [get_current_term()]

    fee_summaries = [calculate_student_fee_summary(student, term) for term in terms]
    payments = FeePayment.objects.select_related("term", "term__academic_year", "recorded_by").filter(student=student)
    return render(
        request,
        "academics/fee_statement.html",
        {
            "student": student,
            "fee_summaries": fee_summaries,
            "payments": payments,
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def fee_overview_view(request):
    selected_term = request.GET.get("term", "").strip()
    query = request.GET.get("q", "").strip()
    fee_structures = FeeStructure.objects.select_related("term", "term__academic_year")
    payments = FeePayment.objects.select_related("student", "term", "term__academic_year", "recorded_by")

    if selected_term:
        fee_structures = fee_structures.filter(term_id=selected_term)
        payments = payments.filter(term_id=selected_term)
    if query:
        payments = payments.filter(
            Q(student__first_name__icontains=query)
            | Q(student__last_name__icontains=query)
            | Q(student__admission_number__icontains=query)
            | Q(receipt_number__icontains=query)
            | Q(transaction_reference__icontains=query)
        )

    total_collected = payments.aggregate(total=Sum("amount_paid"))["total"] or Decimal("0.00")
    return render(
        request,
        "academics/fee_overview.html",
        {
            "fee_structures": fee_structures,
            "payments": payments[:20],
            "query": query,
            "selected_term": selected_term,
            "terms": Term.objects.select_related("academic_year"),
            "total_collected": total_collected,
            "current_term": get_current_term(),
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def fee_structure_create_view(request):
    form = FeeStructureForm(request.POST or None)
    redirect_response = save_model_form(request, form, "Fee structure created successfully.", "academics:fee_overview")
    if redirect_response:
        return redirect_response
    return render(
        request,
        "academics/config_form.html",
        {
            "form": form,
            "page_title": "Create Fee Structure",
            "submit_label": "Save Structure",
            "cancel_url": reverse("academics:fee_overview"),
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def fee_structure_update_view(request, pk):
    fee_structure = get_object_or_404(FeeStructure.objects.select_related("term", "term__academic_year"), pk=pk)
    form = FeeStructureForm(request.POST or None, instance=fee_structure)
    redirect_response = save_model_form(request, form, "Fee structure updated successfully.", "academics:fee_overview")
    if redirect_response:
        return redirect_response
    return render(
        request,
        "academics/config_form.html",
        {
            "form": form,
            "page_title": "Update Fee Structure",
            "submit_label": "Update Structure",
            "cancel_url": reverse("academics:fee_overview"),
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def fee_structure_delete_view(request, pk):
    fee_structure = get_object_or_404(FeeStructure.objects.select_related("term", "term__academic_year"), pk=pk)
    if request.method == "POST":
        fee_structure.delete()
        messages.success(request, "Fee structure deleted successfully.")
        return redirect("academics:fee_overview")
    return render(
        request,
        "academics/config_confirm_delete.html",
        {
            "item_label": str(fee_structure),
            "item_type": "fee structure",
            "cancel_url": reverse("academics:fee_overview"),
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def fee_payment_create_view(request):
    initial = {}
    if request.GET.get("student"):
        initial["student"] = request.GET["student"]
    if request.GET.get("term"):
        initial["term"] = request.GET["term"]

    form = FeePaymentForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        payment = form.save(commit=False)
        payment.recorded_by = request.user
        payment.save()
        messages.success(request, f"Payment recorded successfully. Receipt {payment.receipt_number} is ready.")
        return redirect("academics:fee_overview")
    return render(
        request,
        "academics/config_form.html",
        {
            "form": form,
            "page_title": "Record Fee Payment",
            "submit_label": "Save Payment",
            "cancel_url": reverse("academics:fee_overview"),
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def fee_payment_update_view(request, pk):
    payment = get_object_or_404(FeePayment.objects.select_related("student", "term", "term__academic_year"), pk=pk)
    form = FeePaymentForm(request.POST or None, instance=payment)
    if request.method == "POST" and form.is_valid():
        updated_payment = form.save(commit=False)
        updated_payment.recorded_by = request.user
        updated_payment.save()
        messages.success(request, "Fee payment updated successfully.")
        return redirect("academics:fee_overview")
    return render(
        request,
        "academics/config_form.html",
        {
            "form": form,
            "page_title": "Update Fee Payment",
            "submit_label": "Update Payment",
            "cancel_url": reverse("academics:fee_overview"),
        },
    )


@login_required
def fee_receipt_pdf_view(request, pk):
    payment = get_object_or_404(FeePayment.objects.select_related("student", "term", "term__academic_year", "recorded_by"), pk=pk)
    if not user_can_access_student_finance(request.user, payment.student):
        raise PermissionDenied

    file_name = f"{slugify(payment.student.full_name)}-{payment.receipt_number.lower()}-{payment.payment_date:%Y%m%d}.pdf"
    pdf_content = build_simple_text_pdf(
        f"{settings.SCHOOL_NAME} Fee Receipt",
        build_fee_receipt_lines(payment),
    )
    response = HttpResponse(pdf_content, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{file_name}"'
    return response


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def assignment_list_view(request):
    assignments = TeachingAssignment.objects.select_related("teacher", "subject", "school_class")
    if get_user_role(request.user) == UserProfile.ROLE_TEACHER:
        assignments = assignments.filter(teacher=getattr(request.user, "teacher_profile", None))
    return render(request, "academics/assignment_list.html", {"assignments": assignments})


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def assignment_create_view(request):
    form = TeachingAssignmentForm(request.POST or None)
    form = configure_assignment_form_for_user(request, form)
    if request.method == "POST" and form.is_valid():
        assignment = form.save(commit=False)
        if get_user_role(request.user) == UserProfile.ROLE_TEACHER:
            assignment.teacher = getattr(request.user, "teacher_profile", None)
        assignment.save()
        messages.success(request, "Teacher assignment created successfully.")
        return redirect("academics:assignment_list")
    return render(
        request,
        "academics/assignment_form.html",
        {"form": form, "page_title": "Assign Teacher", "submit_label": "Save Assignment"},
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def assignment_update_view(request, pk):
    assignment = get_object_or_404(TeachingAssignment, pk=pk)
    if get_user_role(request.user) == UserProfile.ROLE_TEACHER and assignment.teacher != getattr(
        request.user,
        "teacher_profile",
        None,
    ):
        raise PermissionDenied
    form = TeachingAssignmentForm(request.POST or None, instance=assignment)
    form = configure_assignment_form_for_user(request, form)
    if request.method == "POST" and form.is_valid():
        assignment = form.save(commit=False)
        if get_user_role(request.user) == UserProfile.ROLE_TEACHER:
            assignment.teacher = getattr(request.user, "teacher_profile", None)
        assignment.save()
        messages.success(request, "Teacher assignment updated successfully.")
        return redirect("academics:assignment_list")
    return render(
        request,
        "academics/assignment_form.html",
        {"form": form, "page_title": "Update Assignment", "submit_label": "Update Assignment"},
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def assignment_delete_view(request, pk):
    assignment = get_object_or_404(TeachingAssignment, pk=pk)
    if get_user_role(request.user) == UserProfile.ROLE_TEACHER and assignment.teacher != getattr(
        request.user,
        "teacher_profile",
        None,
    ):
        raise PermissionDenied
    if request.method == "POST":
        assignment.delete()
        messages.success(request, "Teacher assignment deleted successfully.")
        return redirect("academics:assignment_list")
    return render(request, "academics/assignment_confirm_delete.html", {"assignment": assignment})


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def attendance_mark_view(request):
    form_source = request.POST if request.method == "POST" else request.GET or None
    form = AttendanceSelectionForm(form_source)
    attendance_rows = []
    attendance_register = None
    attendance_summary = None
    selected_class = None
    selected_date = None

    if form.is_valid():
        selected_class = form.cleaned_data["school_class"]
        selected_date = form.cleaned_data["date"]
        if get_user_role(request.user) == UserProfile.ROLE_TEACHER and not teacher_can_access_class(request.user, selected_class):
            raise PermissionDenied

        if request.method == "POST":
            action = request.POST.get("action", "manual_save")
            attendance_register, _ = persist_attendance_entries(
                selected_class,
                selected_date,
                request.user,
                request.POST,
                AttendanceRegister.SAVE_MODE_MANUAL,
            )
            if action == "save_download":
                return build_attendance_pdf_response(selected_class, selected_date, attendance_register)
            messages.success(request, "Attendance saved successfully.")
            redirect_url = f"{reverse('academics:attendance_mark')}?school_class={selected_class.pk}&date={selected_date.isoformat()}"
            return redirect(redirect_url)

        attendance_rows = build_attendance_rows(selected_class, selected_date)
        attendance_summary = summarize_attendance_rows(attendance_rows)
        attendance_register = AttendanceRegister.objects.select_related("saved_by").filter(
            school_class=selected_class,
            date=selected_date,
        ).first()

    return render(
        request,
        "academics/attendance_form.html",
        {
            "form": form,
            "attendance_rows": attendance_rows,
            "attendance_register": attendance_register,
            "attendance_summary": attendance_summary,
            "selected_class": selected_class,
            "selected_date": selected_date,
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
@require_POST
def attendance_autosave_view(request):
    form = AttendanceSelectionForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"saved": False, "errors": form.errors}, status=400)

    selected_class = form.cleaned_data["school_class"]
    selected_date = form.cleaned_data["date"]
    if get_user_role(request.user) == UserProfile.ROLE_TEACHER and not teacher_can_access_class(request.user, selected_class):
        raise PermissionDenied

    attendance_register, summary = persist_attendance_entries(
        selected_class,
        selected_date,
        request.user,
        request.POST,
        AttendanceRegister.SAVE_MODE_AUTO,
    )
    saved_by = attendance_register.saved_by.get_full_name() or attendance_register.saved_by.username
    return JsonResponse(
        {
            "saved": True,
            "saved_at": timezone.localtime(attendance_register.last_saved_at).strftime("%Y-%m-%d %H:%M"),
            "saved_by": saved_by,
            "save_mode": attendance_register.get_save_mode_display(),
            "summary": summary,
        }
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def attendance_export_pdf_view(request):
    form = AttendanceSelectionForm(request.GET or None)
    if not form.is_valid():
        messages.error(request, "Select a class and date before downloading the attendance register.")
        return redirect("academics:attendance_mark")

    selected_class = form.cleaned_data["school_class"]
    selected_date = form.cleaned_data["date"]
    if get_user_role(request.user) == UserProfile.ROLE_TEACHER and not teacher_can_access_class(request.user, selected_class):
        raise PermissionDenied

    attendance_register = AttendanceRegister.objects.filter(school_class=selected_class, date=selected_date).first()
    if not attendance_register:
        summary = summarize_attendance_records(
            AttendanceRecord.objects.filter(school_class=selected_class, date=selected_date)
        )
        attendance_register, _ = AttendanceRegister.objects.update_or_create(
            school_class=selected_class,
            date=selected_date,
            defaults={
                "saved_by": request.user,
                "save_mode": AttendanceRegister.SAVE_MODE_MANUAL,
                "total_students": summary["total"],
                "present_count": summary["present"],
                "absent_count": summary["absent"],
                "late_count": summary["late"],
                "excused_count": summary["excused"],
            },
        )
    return build_attendance_pdf_response(selected_class, selected_date, attendance_register)


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def attendance_records_view(request):
    form = AttendanceSelectionForm(request.GET or None)
    records = AttendanceRecord.objects.select_related("student", "school_class", "marked_by")
    attendance_register = None
    attendance_summary = None
    selected_class = None
    selected_date = None

    if form.is_valid():
        selected_class = form.cleaned_data["school_class"]
        selected_date = form.cleaned_data["date"]
        if get_user_role(request.user) == UserProfile.ROLE_TEACHER and not teacher_can_access_class(request.user, selected_class):
            raise PermissionDenied
        records = records.filter(school_class=selected_class, date=selected_date)
        attendance_register = AttendanceRegister.objects.select_related("saved_by").filter(
            school_class=selected_class,
            date=selected_date,
        ).first()
        attendance_summary = (
            {
                "total": attendance_register.total_students,
                "present": attendance_register.present_count,
                "absent": attendance_register.absent_count,
                "late": attendance_register.late_count,
                "excused": attendance_register.excused_count,
            }
            if attendance_register
            else summarize_attendance_records(records)
        )
    else:
        records = records.none()

    return render(
        request,
        "academics/attendance_list.html",
        {
            "form": form,
            "records": records,
            "attendance_register": attendance_register,
            "attendance_summary": attendance_summary,
            "selected_class": selected_class,
            "selected_date": selected_date,
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def grade_upload_view(request):
    form_source = request.POST if request.method == "POST" else request.GET or None
    form = GradeUploadForm(form_source)
    grade_rows = []
    selected_class = None
    selected_exam_type = None
    selected_subject = None
    selected_term = None
    selected_term_record = None

    if form.is_valid():
        selected_class = form.cleaned_data["school_class"]
        selected_subject = form.cleaned_data["subject"]
        selected_term = form.cleaned_data["term"]
        selected_term_record = form.cleaned_data["term_record"]
        selected_exam_type = form.cleaned_data["examination_type"]
        if get_user_role(request.user) == UserProfile.ROLE_TEACHER and not teacher_can_upload_subject_grade(
            request.user,
            selected_class,
            selected_subject,
        ):
            raise PermissionDenied

        students = Student.objects.filter(current_class=selected_class).order_by("first_name", "last_name")
        existing_grades = {
            grade.student_id: grade
            for grade in Grade.objects.filter(
                school_class=selected_class,
                subject=selected_subject,
                term=selected_term,
                examination_type=selected_exam_type,
            )
        }
        grade_rows = [
            {
                "student": student,
                "ca_score": existing_grades.get(student.id).ca_score if student.id in existing_grades else 0,
                "exam_score": existing_grades.get(student.id).exam_score if student.id in existing_grades else 0,
                "remarks": existing_grades.get(student.id).remarks if student.id in existing_grades else "",
                "total_score": existing_grades.get(student.id).total_score if student.id in existing_grades else 0,
            }
            for student in students
        ]

        if request.method == "POST":
            teacher = getattr(request.user, "teacher_profile", None)
            for row in grade_rows:
                student = row["student"]
                ca_score = safe_decimal(request.POST.get(f"ca_{student.id}", "0"), 40)
                exam_score = safe_decimal(request.POST.get(f"exam_{student.id}", "0"), 60)
                remarks = request.POST.get(f"remarks_{student.id}", "")
                Grade.objects.update_or_create(
                    student=student,
                    subject=selected_subject,
                    term=selected_term,
                    examination_type=selected_exam_type,
                    defaults={
                        "school_class": selected_class,
                        "term_record": selected_term_record,
                        "teacher": teacher,
                        "ca_score": ca_score,
                        "exam_score": exam_score,
                        "remarks": remarks,
                    },
                )
            messages.success(request, "Grades uploaded successfully.")
            redirect_url = "{}?{}".format(
                reverse("academics:grade_upload"),
                urlencode(
                    {
                        "school_class": selected_class.pk,
                        "subject": selected_subject.pk,
                        "term": selected_term,
                        "term_record": selected_term_record.pk if selected_term_record else "",
                        "examination_type": selected_exam_type.pk,
                    }
                ),
            )
            return redirect(redirect_url)

    return render(
        request,
        "academics/grade_form.html",
        {
            "form": form,
            "grade_rows": grade_rows,
            "selected_class": selected_class,
            "selected_exam_type": selected_exam_type,
            "selected_subject": selected_subject,
            "selected_term": selected_term,
            "selected_term_record": selected_term_record,
        },
    )


@login_required
def grade_list_view(request):
    role = get_user_role(request.user)
    exam_type = request.GET.get("exam_type", "").strip()
    term = request.GET.get("term", "").strip()
    student_filter = request.GET.get("student", "").strip()
    grades = Grade.objects.select_related("student", "subject", "school_class", "teacher", "examination_type", "term_record")
    student_choices = []

    if role == UserProfile.ROLE_STUDENT:
        grades = grades.filter(student=getattr(request.user, "student_profile", None))
    elif role == UserProfile.ROLE_TEACHER:
        grades = grades.filter(teacher=getattr(request.user, "teacher_profile", None))
    elif role == UserProfile.ROLE_PARENT:
        linked_students = getattr(request.user, "parent_profile", None)
        if not linked_students:
            raise PermissionDenied
        student_choices = list(linked_students.students.order_by("first_name", "last_name"))
        grades = grades.filter(student__in=student_choices)
        if student_filter:
            grades = grades.filter(student_id=student_filter)
    elif role != UserProfile.ROLE_ADMIN:
        raise PermissionDenied

    if term:
        grades = grades.filter(term=term)
    if exam_type:
        grades = grades.filter(examination_type_id=exam_type)

    return render(
        request,
        "academics/grade_list.html",
        {
            "grades": grades,
            "term": term,
            "exam_type": exam_type,
            "student_filter": student_filter,
            "student_choices": student_choices,
            "exam_types": ExaminationType.objects.all(),
            "term_choices": Grade.TERM_CHOICES,
        },
    )


@login_required
def note_list_view(request):
    role = get_user_role(request.user)
    query = request.GET.get("q", "").strip()
    student_filter = request.GET.get("student", "").strip()
    notes = ClassNote.objects.select_related("school_class", "subject", "uploaded_by", "uploaded_by__user")
    student_choices = []

    if role == UserProfile.ROLE_ADMIN:
        pass
    elif role == UserProfile.ROLE_TEACHER:
        teacher = getattr(request.user, "teacher_profile", None)
        if not teacher:
            raise PermissionDenied
        notes = notes.filter(
            Q(uploaded_by=teacher)
            | Q(school_class__class_teacher=teacher)
            | Q(school_class__teaching_assignments__teacher=teacher)
        ).distinct()
    elif role == UserProfile.ROLE_STUDENT:
        student = getattr(request.user, "student_profile", None)
        current_class = getattr(student, "current_class", None)
        notes = notes.filter(school_class=current_class, is_published=True) if current_class else notes.none()
    elif role == UserProfile.ROLE_PARENT:
        parent = getattr(request.user, "parent_profile", None)
        if not parent:
            raise PermissionDenied
        student_choices = list(parent.students.select_related("current_class").order_by("first_name", "last_name"))
        if student_filter:
            selected_student = next((student for student in student_choices if str(student.pk) == student_filter), None)
            current_class = getattr(selected_student, "current_class", None)
            notes = notes.filter(school_class=current_class, is_published=True) if current_class else notes.none()
        else:
            notes = notes.filter(
                school_class__in=[student.current_class for student in student_choices if student.current_class_id],
                is_published=True,
            )
    else:
        raise PermissionDenied

    if query:
        notes = notes.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(subject__name__icontains=query)
            | Q(school_class__name__icontains=query)
            | Q(school_class__section__icontains=query)
        )

    return render(
        request,
        "academics/note_list.html",
        {
            "notes": notes,
            "query": query,
            "student_filter": student_filter,
            "student_choices": student_choices,
            "can_manage_notes": role in {UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER},
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def note_create_view(request):
    form = ClassNoteForm(request.POST or None, request.FILES or None)
    form = configure_note_form_for_user(request, form)
    if request.method == "POST" and form.is_valid():
        note = form.save(commit=False)
        if get_user_role(request.user) == UserProfile.ROLE_TEACHER:
            if not teacher_can_access_class(request.user, note.school_class):
                raise PermissionDenied
            note.uploaded_by = getattr(request.user, "teacher_profile", None)
        note.save()
        messages.success(request, "Class note uploaded successfully.")
        return redirect("academics:note_list")
    return render(
        request,
        "academics/note_form.html",
        {"form": form, "page_title": "Upload Class Note", "submit_label": "Publish Note"},
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def note_update_view(request, pk):
    note = get_object_or_404(ClassNote.objects.select_related("uploaded_by"), pk=pk)
    if get_user_role(request.user) == UserProfile.ROLE_TEACHER and note.uploaded_by != getattr(
        request.user,
        "teacher_profile",
        None,
    ):
        raise PermissionDenied
    form = ClassNoteForm(request.POST or None, request.FILES or None, instance=note)
    form = configure_note_form_for_user(request, form)
    if request.method == "POST" and form.is_valid():
        updated_note = form.save(commit=False)
        if get_user_role(request.user) == UserProfile.ROLE_TEACHER:
            updated_note.uploaded_by = getattr(request.user, "teacher_profile", None)
        updated_note.save()
        messages.success(request, "Class note updated successfully.")
        return redirect("academics:note_list")
    return render(
        request,
        "academics/note_form.html",
        {"form": form, "page_title": "Update Class Note", "submit_label": "Update Note"},
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def note_delete_view(request, pk):
    note = get_object_or_404(ClassNote.objects.select_related("uploaded_by"), pk=pk)
    if get_user_role(request.user) == UserProfile.ROLE_TEACHER and note.uploaded_by != getattr(
        request.user,
        "teacher_profile",
        None,
    ):
        raise PermissionDenied
    if request.method == "POST":
        note.delete()
        messages.success(request, "Class note deleted successfully.")
        return redirect("academics:note_list")
    return render(request, "academics/note_confirm_delete.html", {"note": note})


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def grade_delete_view(request, pk):
    grade = get_object_or_404(Grade.objects.select_related("teacher"), pk=pk)
    if get_user_role(request.user) == UserProfile.ROLE_TEACHER and grade.teacher != getattr(request.user, "teacher_profile", None):
        raise PermissionDenied
    if request.method == "POST":
        grade.delete()
        messages.success(request, "Grade record deleted successfully.")
        return redirect("academics:grade_list")
    return render(request, "academics/grade_confirm_delete.html", {"grade": grade})
