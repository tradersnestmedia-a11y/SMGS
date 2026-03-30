from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import UserProfile
from accounts.permissions import get_user_role, role_required

from .forms import TeacherCreateForm, TeacherUpdateForm
from .models import Teacher


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER)
def teacher_list_view(request):
    query = request.GET.get("q", "").strip()
    teachers = Teacher.objects.select_related("user")
    if query:
        teachers = teachers.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(employee_id__icontains=query)
            | Q(specialization__icontains=query)
        )
    return render(request, "teachers/teacher_list.html", {"teachers": teachers, "query": query})


@login_required
def teacher_detail_view(request, pk):
    teacher = get_object_or_404(Teacher.objects.select_related("user"), pk=pk)
    role = get_user_role(request.user)
    if role == UserProfile.ROLE_TEACHER and teacher.user != request.user:
        raise PermissionDenied
    if role not in {UserProfile.ROLE_ADMIN, UserProfile.ROLE_TEACHER}:
        raise PermissionDenied
    return render(request, "teachers/teacher_detail.html", {"teacher": teacher})


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def teacher_create_view(request):
    form = TeacherCreateForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            form.save()
        messages.success(request, "Teacher created successfully.")
        return redirect("teachers:list")
    return render(
        request,
        "teachers/teacher_form.html",
        {"form": form, "page_title": "Add Teacher", "submit_label": "Save Teacher"},
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def teacher_update_view(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    form = TeacherUpdateForm(request.POST or None, request.FILES or None, instance=teacher)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            form.save()
        messages.success(request, "Teacher updated successfully.")
        return redirect("teachers:detail", pk=teacher.pk)
    return render(
        request,
        "teachers/teacher_form.html",
        {"form": form, "page_title": "Update Teacher", "submit_label": "Update Teacher"},
    )


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def teacher_delete_view(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == "POST":
        teacher.user.delete()
        messages.success(request, "Teacher deleted successfully.")
        return redirect("teachers:list")
    return render(request, "teachers/teacher_confirm_delete.html", {"teacher": teacher})
