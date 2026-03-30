from django.contrib import admin

from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("admission_number", "first_name", "last_name", "current_class", "joined_on")
    list_filter = ("gender", "current_class")
    search_fields = ("admission_number", "first_name", "last_name", "email")
