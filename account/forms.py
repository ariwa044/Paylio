from django import forms
from .models import KYC
from django.forms import ImageField, FileInput, DateInput



class DateInput(forms.DateInput):
    input_type = 'date'


class KYCForm(forms.ModelForm):
    identity_image = ImageField(widget=FileInput)
    image = ImageField(widget=FileInput)
    signature = ImageField(widget=FileInput)


    class Meta:
        model = KYC
        fields = [
            'full_name',
            'image',
            'marital_status',
            'gender',
            'identity_type',
            'identity_image',
            'date_of_birth',
            'signature',
            'country',
            'state',
            'city',
            'mobile',
            'mothers_maiden_name',

        ] 

        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder":"Full Name"}),
            "mobile": forms.TextInput(attrs={"placeholder":"Mobile Number"}),
            "mothers_maiden_name": forms.TextInput(attrs={"placeholder":"Mother's Maiden Name"}),
            "country": forms.TextInput(attrs={"placeholder":"Country"}),
            "state": forms.TextInput(attrs={"placeholder":"State"}),
            "city": forms.TextInput(attrs={"placeholder":"City"}),
            'date_of_birth': DateInput,
            'marital_status': forms.Select(attrs={"class": "kyc-select"}),
            'gender': forms.Select(attrs={"class": "kyc-select"}),
            'identity_type': forms.Select(attrs={"class": "kyc-select"}),
        }   