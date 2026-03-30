from django.contrib import admin

from .models import NotificationLog, StaffRegistration, StudentRegistration, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "phone", "photo", "created_at")
    list_filter = ("role",)
    search_fields = ("user__username", "user__first_name", "user__last_name")


@admin.register(StudentRegistration)
class StudentRegistrationAdmin(admin.ModelAdmin):
    list_display = ("student_id", "full_name", "target_grade", "status", "email_sent", "personal_email", "created_at")
    list_filter = ("status", "target_grade", "email_sent", "created_at")
    search_fields = ("student_id", "full_name", "personal_email", "guardian_name")
    readonly_fields = ("student_id", "created_at", "updated_at", "reviewed_at")


@admin.register(StaffRegistration)
class StaffRegistrationAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "full_name", "department", "position_applying_for", "status", "email_sent", "created_at")
    list_filter = ("status", "department", "email_sent", "created_at")
    search_fields = ("employee_id", "full_name", "personal_email", "department")
    readonly_fields = ("employee_id", "created_at", "updated_at", "reviewed_at")


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ("channel", "status", "recipient", "created_at")
    list_filter = ("channel", "status", "created_at")
    search_fields = ("recipient", "subject", "response_message")
