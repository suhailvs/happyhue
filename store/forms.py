from django import forms
from django.core.validators import RegexValidator

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat", "Haryana",
    "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana",
    "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal", "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
]


class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=120, label="Full name")
    email = forms.EmailField(label="Email")
    phone = forms.CharField(
        max_length=10, label="Mobile number",
        validators=[RegexValidator(r"^[6-9]\d{9}$", "Enter a 10 digit Indian mobile number.")],
    )
    address_line1 = forms.CharField(max_length=200, label="Address")
    address_line2 = forms.CharField(max_length=200, required=False, label="Apartment, landmark (optional)")
    city = forms.CharField(max_length=80, label="City")
    state = forms.ChoiceField(choices=[("", "Select state")] + [(s, s) for s in INDIAN_STATES], label="State")
    pincode = forms.CharField(
        max_length=6, label="PIN code",
        validators=[RegexValidator(r"^[1-9]\d{5}$", "Enter a valid 6 digit PIN code.")],
    )
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}), label="Order notes (optional)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = "form-select" if isinstance(field, forms.ChoiceField) else "form-control"
            field.widget.attrs["class"] = css
        self.fields["phone"].widget.attrs.update(inputmode="numeric", autocomplete="tel-national")
        self.fields["pincode"].widget.attrs.update(inputmode="numeric", autocomplete="postal-code")
        self.fields["email"].widget.attrs["autocomplete"] = "email"
        self.fields["full_name"].widget.attrs["autocomplete"] = "name"
