from django import forms
from django.core.validators import RegexValidator
from .models import Address

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat", "Haryana",
    "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana",
    "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal", "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
]




class AddressForm(forms.ModelForm):
    pincode = forms.CharField(max_length=6, validators=[RegexValidator(r"^\d{6}$", "Enter a 6 digit pincode.")])
    state = forms.ChoiceField(choices=[("", "Select state")] + [(s, s) for s in INDIAN_STATES])
    class Meta:
        model = Address
        fields = ["full_name", "phone", "address_line1", "address_line2", "city", "state", "pincode", "is_default"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, f in self.fields.items():
            # f.widget.attrs["class"] = "form-check-input" if name == "is_default" else "form-control"
            if name == "is_default":
                f.widget.attrs["class"] = "form-check-input"
            elif name == "state":
                f.widget.attrs["class"] = "form-select"
            else:
                f.widget.attrs["class"] = "form-control"
