from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from academics.models import (
    AttendanceRecord,
    ClassNote,
    FeePayment,
    Grade,
    SchoolClass,
    Subject,
    TeachingAssignment,
    Term,
    calculate_student_fee_summary,
    get_current_term,
)
from students.models import Student
from teachers.models import Teacher

from .forms import (
    AccountProfileForm,
    LoginForm,
    ParentCreateForm,
    ParentUpdateForm,
    RegistrationDecisionForm,
    StaffRegistrationEmploymentForm,
    StaffRegistrationPersonalForm,
    StudentRegistrationAcademicForm,
    StudentRegistrationDocumentsForm,
    StudentRegistrationGuardianForm,
    StudentRegistrationPersonalForm,
    StudentRegistrationTargetForm,
)
from .models import ParentProfile, StaffRegistration, StudentRegistration, UserProfile
from .permissions import get_user_role, parent_can_access_student, role_required
from .services import approve_staff_registration, approve_student_registration, create_parent_account, reject_registration

STUDENT_REGISTRATION_STEPS = [
    ("personal", "Personal Info", StudentRegistrationPersonalForm),
    ("guardian", "Guardian Info", StudentRegistrationGuardianForm),
    ("academic", "Academic History", StudentRegistrationAcademicForm),
    ("target", "Target Enrollment", StudentRegistrationTargetForm),
    ("documents", "Documents", StudentRegistrationDocumentsForm),
]

STAFF_REGISTRATION_STEPS = [
    ("personal", "Personal Info", StaffRegistrationPersonalForm),
    ("employment", "Employment Details", StaffRegistrationEmploymentForm),
]

STUDENT_SESSION_KEY = "student_registration_wizard"
STAFF_SESSION_KEY = "staff_registration_wizard"
REGISTRATION_NOTICE_KEY = "latest_registration_notice"


def get_parent_students(user):
    parent_profile = getattr(user, "parent_profile", None)
    if not parent_profile:
        return Student.objects.none()
    return parent_profile.students.select_related("current_class", "user").order_by("first_name", "last_name")


def get_terms_with_fee_activity(student):
    activity_term_ids = set(
        FeePayment.objects.filter(student=student).values_list("term_id", flat=True)
    )
    if student.grade_level:
        activity_term_ids.update(
            Term.objects.filter(fee_structures__grade_level=student.grade_level).values_list("id", flat=True)
        )
    if not activity_term_ids:
        current_term = get_current_term()
        return [current_term] if current_term else []
    return list(Term.objects.select_related("academic_year").filter(pk__in=activity_term_ids).order_by("-academic_year__year", "-term_number"))


def build_student_portal_snapshot(student, current_term=None):
    selected_term = current_term or get_current_term()
    fee_summary = calculate_student_fee_summary(student, selected_term) if selected_term else None
    current_class = getattr(student, "current_class", None)
    return {
        "student": student,
        "current_term": selected_term,
        "fee_summary": fee_summary,
        "grade_count": Grade.objects.filter(student=student).count(),
        "attendance_count": AttendanceRecord.objects.filter(student=student).count(),
        "note_count": ClassNote.objects.filter(school_class=current_class, is_published=True).count() if current_class else 0,
    }


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    return redirect("accounts:login")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}.")
            return redirect("accounts:dashboard")
        messages.error(request, "Invalid username or password.")

    return render(request, "accounts/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("accounts:login")


def get_step_map(step_config):
    return {key: {"title": title, "form_class": form_class} for key, title, form_class in step_config}


def build_step_items(step_config, current_step, session_data):
    items = []
    for index, (key, title, _) in enumerate(step_config, start=1):
        items.append(
            {
                "key": key,
                "title": title,
                "number": index,
                "is_active": key == current_step,
                "is_complete": key in session_data,
            }
        )
    return items


def get_previous_step(step_config, current_step):
    keys = [key for key, _, _ in step_config]
    index = keys.index(current_step)
    return keys[index - 1] if index > 0 else keys[0]


def get_next_step(step_config, current_step):
    keys = [key for key, _, _ in step_config]
    index = keys.index(current_step)
    return keys[index + 1] if index < len(keys) - 1 else None


def get_first_incomplete_step(step_config, session_data):
    for key, _, _ in step_config:
        if key not in session_data:
            return key
    return step_config[0][0]


def serialize_step_data(cleaned_data):
    serialized = {}
    for key, value in cleaned_data.items():
        if isinstance(value, date):
            serialized[key] = value.isoformat()
        else:
            serialized[key] = value
    return serialized


def hydrate_student_session_data(session_data):
    merged = {}
    for step_values in session_data.values():
        merged.update(step_values)
    if "date_of_birth" in merged and isinstance(merged["date_of_birth"], str):
        merged["date_of_birth"] = date.fromisoformat(merged["date_of_birth"])
    return merged


def hydrate_staff_session_data(session_data):
    merged = {}
    for step_values in session_data.values():
        merged.update(step_values)
    return merged


def student_registration_view(request):
    session_data = request.session.get(STUDENT_SESSION_KEY, {})
    step_map = get_step_map(STUDENT_REGISTRATION_STEPS)
    current_step = request.GET.get("step", STUDENT_REGISTRATION_STEPS[0][0])
    if current_step not in step_map:
        current_step = STUDENT_REGISTRATION_STEPS[0][0]

    required_step = get_first_incomplete_step(STUDENT_REGISTRATION_STEPS, session_data)
    if current_step != STUDENT_REGISTRATION_STEPS[0][0]:
        ordered_keys = [key for key, _, _ in STUDENT_REGISTRATION_STEPS]
        if ordered_keys.index(current_step) > ordered_keys.index(required_step):
            return redirect(f"{reverse('accounts:student_register')}?step={required_step}")

    form_class = step_map[current_step]["form_class"]

    if request.method == "POST":
        current_step = request.POST.get("current_step", current_step)
        action = request.POST.get("action", "next")
        form_class = step_map[current_step]["form_class"]
        form = form_class(request.POST, request.FILES or None)

        if action == "back":
            previous_step = get_previous_step(STUDENT_REGISTRATION_STEPS, current_step)
            return redirect(f"{reverse('accounts:student_register')}?step={previous_step}")

        if form.is_valid():
            if current_step == STUDENT_REGISTRATION_STEPS[-1][0]:
                registration_data = hydrate_student_session_data(session_data)
                registration_data.update(form.cleaned_data)
                registration = StudentRegistration.objects.create(**registration_data)
                request.session.pop(STUDENT_SESSION_KEY, None)
                request.session[REGISTRATION_NOTICE_KEY] = {
                    "type": "Student",
                    "identifier": registration.student_id,
                    "status": "PENDING_ADMIN",
                }
                return redirect("accounts:registration_success")

            session_data[current_step] = serialize_step_data(form.cleaned_data)
            request.session[STUDENT_SESSION_KEY] = session_data
            next_step = get_next_step(STUDENT_REGISTRATION_STEPS, current_step)
            return redirect(f"{reverse('accounts:student_register')}?step={next_step}")
    else:
        form = form_class(initial=session_data.get(current_step, {}))

    return render(
        request,
        "accounts/student_registration.html",
        {
            "form": form,
            "step_items": build_step_items(STUDENT_REGISTRATION_STEPS, current_step, session_data),
            "current_step": current_step,
            "current_title": step_map[current_step]["title"],
            "is_final_step": current_step == STUDENT_REGISTRATION_STEPS[-1][0],
            "back_step": get_previous_step(STUDENT_REGISTRATION_STEPS, current_step),
        },
    )


def staff_registration_view(request):
    session_data = request.session.get(STAFF_SESSION_KEY, {})
    step_map = get_step_map(STAFF_REGISTRATION_STEPS)
    current_step = request.GET.get("step", STAFF_REGISTRATION_STEPS[0][0])
    if current_step not in step_map:
        current_step = STAFF_REGISTRATION_STEPS[0][0]

    required_step = get_first_incomplete_step(STAFF_REGISTRATION_STEPS, session_data)
    if current_step != STAFF_REGISTRATION_STEPS[0][0]:
        ordered_keys = [key for key, _, _ in STAFF_REGISTRATION_STEPS]
        if ordered_keys.index(current_step) > ordered_keys.index(required_step):
            return redirect(f"{reverse('accounts:staff_register')}?step={required_step}")

    form_class = step_map[current_step]["form_class"]

    if request.method == "POST":
        current_step = request.POST.get("current_step", current_step)
        action = request.POST.get("action", "next")
        form_class = step_map[current_step]["form_class"]
        form = form_class(request.POST, request.FILES or None)

        if action == "back":
            previous_step = get_previous_step(STAFF_REGISTRATION_STEPS, current_step)
            return redirect(f"{reverse('accounts:staff_register')}?step={previous_step}")

        if form.is_valid():
            if current_step == STAFF_REGISTRATION_STEPS[-1][0]:
                registration_data = hydrate_staff_session_data(session_data)
                registration_data.update(form.cleaned_data)
                registration = StaffRegistration.objects.create(**registration_data)
                request.session.pop(STAFF_SESSION_KEY, None)
                request.session[REGISTRATION_NOTICE_KEY] = {
                    "type": "Staff",
                    "identifier": registration.employee_id,
                    "status": "PENDING_ADMIN",
                }
                return redirect("accounts:registration_success")

            session_data[current_step] = serialize_step_data(form.cleaned_data)
            request.session[STAFF_SESSION_KEY] = session_data
            next_step = get_next_step(STAFF_REGISTRATION_STEPS, current_step)
            return redirect(f"{reverse('accounts:staff_register')}?step={next_step}")
    else:
        form = form_class(initial=session_data.get(current_step, {}))

    return render(
        request,
        "accounts/staff_registration.html",
        {
            "form": form,
            "step_items": build_step_items(STAFF_REGISTRATION_STEPS, current_step, session_data),
            "current_step": current_step,
            "current_title": step_map[current_step]["title"],
            "is_final_step": current_step == STAFF_REGISTRATION_STEPS[-1][0],
            "back_step": get_previous_step(STAFF_REGISTRATION_STEPS, current_step),
        },
    )


def registration_success_view(request):
    notice = request.session.pop(REGISTRATION_NOTICE_KEY, None)
    return render(request, "accounts/registration_success.html", {"notice": notice})


@login_required
def account_profile_view(request):
    form = AccountProfileForm(request.POST or None, request.FILES or None, user=request.user)
    role = get_user_role(request.user)
    profile_target_url = None

    if role == UserProfile.ROLE_STUDENT and hasattr(request.user, "student_profile"):
        profile_target_url = reverse("students:detail", kwargs={"pk": request.user.student_profile.pk})
    elif role == UserProfile.ROLE_TEACHER and hasattr(request.user, "teacher_profile"):
        profile_target_url = reverse("teachers:detail", kwargs={"pk": request.user.teacher_profile.pk})
    elif role == UserProfile.ROLE_PARENT and hasattr(request.user, "parent_profile"):
        profile_target_url = reverse("accounts:parent_children")

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your account profile has been updated successfully.")
        return redirect("accounts:profile")

    return render(
        request,
        "accounts/profile_settings.html",
        {
            "form": form,
            "profile_target_url": profile_target_url,
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def registration_dashboard_view(request):
    pending_students = StudentRegistration.objects.filter(status=StudentRegistration.STATUS_PENDING)
    pending_staff = StaffRegistration.objects.filter(status=StaffRegistration.STATUS_PENDING)
    recent_students = StudentRegistration.objects.exclude(status=StudentRegistration.STATUS_PENDING)[:8]
    recent_staff = StaffRegistration.objects.exclude(status=StaffRegistration.STATUS_PENDING)[:8]
    return render(
        request,
        "accounts/registration_dashboard.html",
        {
            "pending_students": pending_students,
            "pending_staff": pending_staff,
            "recent_students": recent_students,
            "recent_staff": recent_staff,
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def student_registration_detail_view(request, pk):
    registration = get_object_or_404(StudentRegistration, pk=pk)
    review_form = RegistrationDecisionForm(request.POST or None)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "approve":
            try:
                approve_student_registration(
                    registration,
                    request.user,
                    request.build_absolute_uri(reverse("accounts:login")),
                )
                messages.success(request, f"Student registration {registration.student_id} approved successfully.")
                return redirect("accounts:student_registration_detail", pk=registration.pk)
            except ValueError as exc:
                messages.error(request, str(exc))
        elif action == "reject" and review_form.is_valid():
            try:
                reject_registration(registration, request.user, review_form.cleaned_data["review_reason"])
                messages.warning(request, f"Student registration {registration.student_id} was rejected.")
                return redirect("accounts:student_registration_detail", pk=registration.pk)
            except ValueError as exc:
                messages.error(request, str(exc))

    return render(
        request,
        "accounts/student_registration_detail.html",
        {
            "registration": registration,
            "review_form": review_form,
            "notification_logs": registration.notification_logs.all(),
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def staff_registration_detail_view(request, pk):
    registration = get_object_or_404(StaffRegistration, pk=pk)
    review_form = RegistrationDecisionForm(request.POST or None)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "approve":
            try:
                approve_staff_registration(
                    registration,
                    request.user,
                    request.build_absolute_uri(reverse("accounts:login")),
                )
                messages.success(request, f"Staff registration {registration.employee_id} approved successfully.")
                return redirect("accounts:staff_registration_detail", pk=registration.pk)
            except ValueError as exc:
                messages.error(request, str(exc))
        elif action == "reject" and review_form.is_valid():
            try:
                reject_registration(registration, request.user, review_form.cleaned_data["review_reason"])
                messages.warning(request, f"Staff registration {registration.employee_id} was rejected.")
                return redirect("accounts:staff_registration_detail", pk=registration.pk)
            except ValueError as exc:
                messages.error(request, str(exc))

    return render(
        request,
        "accounts/staff_registration_detail.html",
        {
            "registration": registration,
            "review_form": review_form,
            "notification_logs": registration.notification_logs.all(),
        },
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def parent_list_view(request):
    query = request.GET.get("q", "").strip()
    parents = ParentProfile.objects.select_related("user").prefetch_related("students__current_class")
    if query:
        parents = parents.filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__username__icontains=query)
            | Q(user__email__icontains=query)
            | Q(phone_number__icontains=query)
            | Q(students__admission_number__icontains=query)
            | Q(students__first_name__icontains=query)
            | Q(students__last_name__icontains=query)
        ).distinct()
    return render(request, "accounts/parent_list.html", {"parents": parents, "query": query})


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def parent_create_view(request):
    initial = {}
    if request.GET.get("student"):
        initial["students"] = [request.GET["student"]]

    form = ParentCreateForm(request.POST or None, request.FILES or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        parent, _, email_sent, response_message = create_parent_account(
            form.cleaned_data,
            request.user,
            request.build_absolute_uri(reverse("accounts:login")),
        )
        if email_sent:
            messages.success(
                request,
                f"Parent account for {parent.full_name} created successfully. Credentials were sent to {parent.user.email}.",
            )
        else:
            messages.warning(
                request,
                f"Parent account created, but credentials email was not sent: {response_message}",
            )
        return redirect("accounts:parent_detail", pk=parent.pk)

    return render(
        request,
        "accounts/parent_form.html",
        {"form": form, "page_title": "Add Parent Account", "submit_label": "Create Parent", "cancel_url": reverse("accounts:parent_list")},
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def parent_update_view(request, pk):
    parent = get_object_or_404(ParentProfile.objects.select_related("user"), pk=pk)
    form = ParentUpdateForm(request.POST or None, request.FILES or None, instance=parent)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Parent account updated successfully.")
        return redirect("accounts:parent_detail", pk=parent.pk)

    return render(
        request,
        "accounts/parent_form.html",
        {"form": form, "page_title": "Update Parent Account", "submit_label": "Save Changes", "cancel_url": reverse("accounts:parent_detail", kwargs={"pk": parent.pk})},
    )


@login_required
def parent_detail_view(request, pk):
    parent = get_object_or_404(ParentProfile.objects.select_related("user"), pk=pk)
    role = get_user_role(request.user)
    if role == UserProfile.ROLE_PARENT and parent.user != request.user:
        raise PermissionDenied
    if role not in {UserProfile.ROLE_ADMIN, UserProfile.ROLE_PARENT}:
        raise PermissionDenied

    current_term = get_current_term()
    linked_students = parent.students.select_related("current_class", "user").order_by("first_name", "last_name")
    student_snapshots = [build_student_portal_snapshot(student, current_term) for student in linked_students]
    recent_payments = FeePayment.objects.select_related("student", "term", "term__academic_year").filter(student__in=linked_students)[:8]
    return render(
        request,
        "accounts/parent_detail.html",
        {
            "parent": parent,
            "student_snapshots": student_snapshots,
            "recent_payments": recent_payments,
            "current_term": current_term,
        },
    )


@login_required
@role_required(UserProfile.ROLE_PARENT)
def parent_children_view(request):
    parent = getattr(request.user, "parent_profile", None)
    linked_students = get_parent_students(request.user)
    current_term = get_current_term()
    student_snapshots = [build_student_portal_snapshot(student, current_term) for student in linked_students]
    recent_payments = FeePayment.objects.select_related("student", "term", "term__academic_year").filter(student__in=linked_students)[:8]
    return render(
        request,
        "accounts/parent_children.html",
        {
            "parent": parent,
            "student_snapshots": student_snapshots,
            "recent_payments": recent_payments,
            "current_term": current_term,
        },
    )


@login_required
@role_required(UserProfile.ROLE_PARENT)
def parent_student_overview_view(request, pk):
    student = get_object_or_404(Student.objects.select_related("current_class", "user"), pk=pk)
    if not parent_can_access_student(request.user, student):
        raise PermissionDenied

    terms = get_terms_with_fee_activity(student)
    fee_summaries = [calculate_student_fee_summary(student, term) for term in terms]
    recent_grades = Grade.objects.select_related("subject", "examination_type").filter(student=student).order_by("-uploaded_at")[:10]
    recent_attendance = AttendanceRecord.objects.select_related("school_class", "marked_by").filter(student=student).order_by("-date")[:10]
    current_class = getattr(student, "current_class", None)
    recent_notes = (
        ClassNote.objects.select_related("subject", "school_class")
        .filter(school_class=current_class, is_published=True)
        .order_by("-created_at")[:10]
        if current_class
        else []
    )
    payment_history = FeePayment.objects.select_related("term", "term__academic_year").filter(student=student)[:10]
    return render(
        request,
        "accounts/parent_student_overview.html",
        {
            "student": student,
            "fee_summaries": fee_summaries,
            "recent_grades": recent_grades,
            "recent_attendance": recent_attendance,
            "recent_notes": recent_notes,
            "payment_history": payment_history,
        },
    )


@login_required
def dashboard_view(request):
    role = get_user_role(request.user)
    context = {"role": role}

    if role == UserProfile.ROLE_ADMIN:
        current_term = get_current_term()
        context.update(
            {
                "student_count": Student.objects.count(),
                "teacher_count": Teacher.objects.count(),
                "parent_count": ParentProfile.objects.count(),
                "class_count": SchoolClass.objects.count(),
                "subject_count": Subject.objects.count(),
                "note_count": ClassNote.objects.count(),
                "attendance_count": AttendanceRecord.objects.count(),
                "grade_count": Grade.objects.count(),
                "fee_payment_total": FeePayment.objects.aggregate(total=Sum("amount_paid"))["total"] or 0,
                "current_term": current_term,
                "pending_student_registrations": StudentRegistration.objects.filter(status=StudentRegistration.STATUS_PENDING).count(),
                "pending_staff_registrations": StaffRegistration.objects.filter(status=StaffRegistration.STATUS_PENDING).count(),
                "recent_grades": Grade.objects.select_related("student", "subject").order_by("-uploaded_at")[:5],
                "recent_notes": ClassNote.objects.select_related("school_class", "subject", "uploaded_by").order_by("-created_at")[:5],
                "recent_fee_payments": FeePayment.objects.select_related("student", "term", "term__academic_year").order_by("-payment_date", "-id")[:5],
                "recent_attendance": AttendanceRecord.objects.select_related("student", "school_class")
                .order_by("-date", "-id")[:8],
            }
        )
    elif role == UserProfile.ROLE_TEACHER:
        teacher = getattr(request.user, "teacher_profile", None)
        assignments = TeachingAssignment.objects.select_related("school_class", "subject").filter(teacher=teacher)
        context.update(
            {
                "teacher": teacher,
                "assignment_count": assignments.count(),
                "grade_count": Grade.objects.filter(teacher=teacher).count(),
                "attendance_count": AttendanceRecord.objects.filter(marked_by=teacher).count(),
                "note_count": ClassNote.objects.filter(uploaded_by=teacher).count(),
                "assignments": assignments[:6],
                "recent_notes": ClassNote.objects.select_related("school_class", "subject")
                .filter(uploaded_by=teacher)
                .order_by("-created_at")[:5],
            }
        )
    else:
        if role == UserProfile.ROLE_PARENT:
            parent = getattr(request.user, "parent_profile", None)
            linked_students = list(get_parent_students(request.user))
            current_term = get_current_term()
            student_snapshots = [build_student_portal_snapshot(student, current_term) for student in linked_students]
            total_balance = sum(
                (snapshot["fee_summary"]["balance"] for snapshot in student_snapshots if snapshot["fee_summary"]),
                Decimal("0.00"),
            )
            context.update(
                {
                    "parent": parent,
                    "linked_student_count": len(linked_students),
                    "payment_count": FeePayment.objects.filter(student__in=linked_students).count(),
                    "current_term": current_term,
                    "total_balance": total_balance,
                    "student_snapshots": student_snapshots,
                    "recent_payments": FeePayment.objects.select_related("student", "term", "term__academic_year")
                    .filter(student__in=linked_students)
                    .order_by("-payment_date", "-id")[:5],
                }
            )
        else:
            student = getattr(request.user, "student_profile", None)
            current_class = getattr(student, "current_class", None)
            current_term = get_current_term()
            context.update(
                {
                    "student": student,
                    "grade_count": Grade.objects.filter(student=student).count() if student else 0,
                    "attendance_count": AttendanceRecord.objects.filter(student=student).count() if student else 0,
                    "results": Grade.objects.select_related("subject").filter(student=student)[:6] if student else [],
                    "note_count": ClassNote.objects.filter(school_class=current_class, is_published=True).count() if current_class else 0,
                    "current_term_fee_summary": calculate_student_fee_summary(student, current_term) if student and current_term else None,
                    "recent_notes": ClassNote.objects.select_related("school_class", "subject")
                    .filter(school_class=current_class, is_published=True)
                    .order_by("-created_at")[:5]
                    if current_class
                    else [],
                }
            )

    return render(request, "accounts/dashboard.html", context)
