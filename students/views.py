from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import UserProfile
from accounts.permissions import get_user_role, role_required

from .forms import StudentCreateForm, StudentUpdateForm
from .models import Student


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def student_list_view(request):
    query = request.GET.get("q", "").strip()
    students = Student.objects.select_related("current_class", "user")
    if query:
        students = students.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(admission_number__icontains=query)
            | Q(current_class__name__icontains=query)
        )
    return render(request, "students/student_list.html", {"students": students, "query": query})


@login_required
def student_detail_view(request, pk):
    student = get_object_or_404(Student.objects.select_related("current_class", "user"), pk=pk)
    role = get_user_role(request.user)
    if role == UserProfile.ROLE_STUDENT and student.user != request.user:
        raise PermissionDenied
    if role not in {UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER, UserProfile.ROLE_STUDENT}:
        raise PermissionDenied
    return render(request, "students/student_detail.html", {"student": student})


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def student_create_view(request):
    form = StudentCreateForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            form.save()
        messages.success(request, "Student created successfully.")
        return redirect("students:list")
    return render(
        request,
        "students/student_form.html",
        {"form": form, "page_title": "Add Student", "submit_label": "Save Student"},
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def student_update_view(request, pk):
    student = get_object_or_404(Student, pk=pk)
    form = StudentUpdateForm(request.POST or None, request.FILES or None, instance=student)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            form.save()
        messages.success(request, "Student updated successfully.")
        return redirect("students:detail", pk=student.pk)
    return render(
        request,
        "students/student_form.html",
        {"form": form, "page_title": "Update Student", "submit_label": "Update Student"},
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def student_delete_view(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == "POST":
        student.user.delete()
        messages.success(request, "Student deleted successfully.")
        return redirect("students:list")
    return render(request, "students/student_confirm_delete.html", {"student": student})
