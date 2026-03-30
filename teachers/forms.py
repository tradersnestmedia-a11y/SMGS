from django import forms
from django.contrib.auth.models import User

from accounts.form_utils import style_form_fields
from accounts.models import UserProfile

from .models import Teacher


class TeacherCreateForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    password1 = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(widget=forms.PasswordInput())
    photo = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"accept": "image/*"}),
        help_text="Upload a profile photo.",
    )

    class Meta:
        model = Teacher
        fields = [
            "employee_id",
            "first_name",
            "last_name",
            "nationality",
            "email",
            "phone",
            "specialization",
            "qualifications",
            "department",
            "position",
            "address",
            "hired_on",
        ]
        widgets = {
            "hired_on": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 3}),
            "qualifications": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already in use.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            raise forms.ValidationError("The two passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        teacher = super().save(commit=False)
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            password=self.cleaned_data["password1"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            email=self.cleaned_data["email"],
        )
        user.profile.role = UserProfile.ROLE_TEACHER
        user.profile.photo = self.cleaned_data.get("photo")
        user.profile.save()
        teacher.user = user
        if commit:
            teacher.save()
        return teacher


class TeacherUpdateForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    photo = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"accept": "image/*"}),
        help_text="Upload a new profile photo if needed.",
    )

    class Meta:
        model = Teacher
        fields = [
            "employee_id",
            "first_name",
            "last_name",
            "nationality",
            "email",
            "phone",
            "specialization",
            "qualifications",
            "department",
            "position",
            "address",
            "hired_on",
        ]
        widgets = {
            "hired_on": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 3}),
            "qualifications": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["username"].initial = self.instance.user.username
            self.fields["photo"].initial = self.instance.user.profile.photo
        style_form_fields(self)

    def clean_username(self):
        username = self.cleaned_data["username"]
        user_qs = User.objects.filter(username=username)
        if self.instance.pk:
            user_qs = user_qs.exclude(pk=self.instance.user.pk)
        if user_qs.exists():
            raise forms.ValidationError("This username is already in use.")
        return username

    def save(self, commit=True):
        teacher = super().save(commit=False)
        user = teacher.user
        user.username = self.cleaned_data["username"]
        user.first_name = teacher.first_name
        user.last_name = teacher.last_name
        user.email = teacher.email
        photo = self.cleaned_data.get("photo")
        if commit:
            user.save()
            if photo:
                user.profile.photo = photo
                user.profile.save()
            teacher.save()
        return teacher
