from django import forms


def style_form_fields(form):
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, (forms.Select, forms.SelectMultiple)):
            base_class = "form-select"
        elif isinstance(widget, forms.CheckboxInput):
            base_class = "form-check-input"
        else:
            base_class = "form-control"

        current_classes = widget.attrs.get("class", "").strip()
        widget.attrs["class"] = f"{current_classes} {base_class}".strip()
