from django.contrib import admin

from .models import Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "first_name", "last_name", "specialization", "hired_on")
    list_filter = ("specialization",)
    search_fields = ("employee_id", "first_name", "last_name", "email")
