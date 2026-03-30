from django.contrib.auth.models import User
from django.db import models


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="teacher_profile")
    employee_id = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    nationality = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    specialization = models.CharField(max_length=150, blank=True)
    qualifications = models.TextField(blank=True)
    department = models.CharField(max_length=150, blank=True)
    position = models.CharField(max_length=150, blank=True)
    address = models.TextField(blank=True)
    hired_on = models.DateField()

    class Meta:
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.employee_id} - {self.full_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
