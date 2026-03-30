from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .form_utils import style_form_fields


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "Username",
                "autofocus": True,
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "Password",
            }
        )
    )


class StudentRegistrationPersonalForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    gender = forms.ChoiceField(choices=tuple((choice, choice) for choice in ("Male", "Female", "Not Specified")))
    nationality = forms.CharField(max_length=100, initial="Zambian")
    zambian_phone = forms.CharField(max_length=20, help_text="Use a valid Zambian phone number.")
    personal_email = forms.EmailField()
    address = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)


class StudentRegistrationGuardianForm(forms.Form):
    guardian_name = forms.CharField(max_length=150)
    guardian_relationship = forms.CharField(max_length=100)
    guardian_phone = forms.CharField(max_length=20)
    guardian_email = forms.EmailField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)


class StudentRegistrationAcademicForm(forms.Form):
    previous_school_attended = forms.CharField(max_length=200)
    last_grade_attended = forms.CharField(max_length=50)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)


class StudentRegistrationTargetForm(forms.Form):
    target_grade = forms.ChoiceField(choices=tuple((f"Grade {grade}", f"Grade {grade}") for grade in range(1, 13)))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)


class StudentRegistrationDocumentsForm(forms.Form):
    profile_photo = forms.FileField(
        required=True,
        widget=forms.ClearableFileInput(attrs={"accept": "image/*"}),
        help_text="Upload a profile picture for the student profile.",
    )
    last_report_card = forms.FileField(required=True)
    birth_certificate = forms.FileField(required=True)
    transfer_letter = forms.FileField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)


class StaffRegistrationPersonalForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    nationality = forms.CharField(max_length=100, initial="Zambian")
    zambian_phone = forms.CharField(max_length=20, help_text="Use a valid Zambian phone number.")
    personal_email = forms.EmailField()
    qualifications = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)


class StaffRegistrationEmploymentForm(forms.Form):
    department = forms.CharField(max_length=150)
    position_applying_for = forms.CharField(max_length=150)
    profile_photo = forms.FileField(
        required=True,
        widget=forms.ClearableFileInput(attrs={"accept": "image/*"}),
        help_text="Upload a profile picture for the staff profile.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)


class RegistrationDecisionForm(forms.Form):
    review_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Optional reason or approval note"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)


class AccountProfileForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    phone = forms.CharField(max_length=20, required=False)
    photo = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"accept": "image/*"}),
        help_text="Upload a new profile picture or clear the current one.",
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields["first_name"].initial = self.user.first_name
            self.fields["last_name"].initial = self.user.last_name
            self.fields["email"].initial = self.user.email
            self.fields["phone"].initial = self.user.profile.phone
            self.fields["photo"].initial = self.user.profile.photo
        style_form_fields(self)

    def save(self):
        self.user.first_name = self.cleaned_data["first_name"]
        self.user.last_name = self.cleaned_data["last_name"]
        self.user.email = self.cleaned_data["email"]
        self.user.save()

        self.user.profile.phone = self.cleaned_data["phone"]
        photo = self.cleaned_data.get("photo")
        if photo is False:
            self.user.profile.photo.delete(save=False)
            self.user.profile.photo = None
        elif photo:
            self.user.profile.photo = photo
        self.user.profile.save()
        return self.user
