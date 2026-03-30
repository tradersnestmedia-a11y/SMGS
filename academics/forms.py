from datetime import date

from django import forms

from accounts.form_utils import style_form_fields

from .models import (
    AcademicYear,
    ClassNote,
    ExaminationType,
    Grade,
    GradingSystem,
    SchoolClass,
    Subject,
    SubjectGradeLevel,
    TeachingAssignment,
    Term,
)


class SchoolClassForm(forms.ModelForm):
    class Meta:
        model = SchoolClass
        fields = ["name", "section", "description", "class_teacher"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["code", "name", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)


class TeachingAssignmentForm(forms.ModelForm):
    class Meta:
        model = TeachingAssignment
        fields = ["school_class", "subject", "teacher"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)


class AttendanceSelectionForm(forms.Form):
    school_class = forms.ModelChoiceField(queryset=SchoolClass.objects.none())
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), initial=date.today)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["school_class"].queryset = SchoolClass.objects.select_related("class_teacher")
        style_form_fields(self)


class GradeUploadForm(forms.Form):
    school_class = forms.ModelChoiceField(queryset=SchoolClass.objects.none())
    subject = forms.ModelChoiceField(queryset=Subject.objects.none())
    term = forms.ChoiceField(choices=[("", "Select term"), *Grade.TERM_CHOICES])
    term_record = forms.ModelChoiceField(queryset=Term.objects.none(), required=False)
    examination_type = forms.ModelChoiceField(queryset=ExaminationType.objects.none())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["school_class"].queryset = SchoolClass.objects.select_related("class_teacher")
        self.fields["subject"].queryset = Subject.objects.all()
        self.fields["term_record"].queryset = Term.objects.select_related("academic_year")
        self.fields["term_record"].empty_label = "Optional linked academic term"
        self.fields["examination_type"].queryset = ExaminationType.objects.all()
        style_form_fields(self)


class ClassNoteForm(forms.ModelForm):
    class Meta:
        model = ClassNote
        fields = ["school_class", "subject", "title", "description", "attachment", "is_published"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "attachment": forms.ClearableFileInput(
                attrs={"accept": ".pdf,.doc,.docx,.ppt,.pptx,.txt,.jpg,.jpeg,.png,.zip"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["school_class"].queryset = SchoolClass.objects.select_related("class_teacher")
        self.fields["subject"].queryset = Subject.objects.all()
        self.fields["subject"].required = False
        style_form_fields(self)


class AcademicYearForm(forms.ModelForm):
    class Meta:
        model = AcademicYear
        fields = ["year", "start_date", "end_date", "is_current"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)


class TermForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = ["academic_year", "term_number", "start_date", "end_date"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["academic_year"].queryset = AcademicYear.objects.all()
        style_form_fields(self)


class ExaminationTypeForm(forms.ModelForm):
    class Meta:
        model = ExaminationType
        fields = ["name", "weight_percentage", "applicable_from_grade", "applicable_to_grade"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["applicable_from_grade"].required = False
        self.fields["applicable_to_grade"].required = False
        style_form_fields(self)


class GradingSystemForm(forms.ModelForm):
    class Meta:
        model = GradingSystem
        fields = ["grade_name", "min_score", "max_score", "remark", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_fields(self)


class SubjectGradeLevelForm(forms.ModelForm):
    class Meta:
        model = SubjectGradeLevel
        fields = ["subject", "grade_level", "is_core"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subject"].queryset = Subject.objects.all()
        style_form_fields(self)
