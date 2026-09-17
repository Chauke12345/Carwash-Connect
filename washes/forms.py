from django import forms

from .models import WashService, Vehicle


# =========================================================
# VEHICLE REGISTRATION FORM
# =========================================================

class VehicleRegistrationForm(forms.Form):

    customer_name = forms.CharField(
        max_length=150,
        label="Customer Name"
    )

    phone_number = forms.CharField(
        max_length=20,
        label="Phone Number"
    )

    registration_number = forms.CharField(
        max_length=30,
        label="Vehicle Registration"
    )

    vehicle_make = forms.CharField(
        max_length=100,
        required=False,
        label="Vehicle Make"
    )

    vehicle_model = forms.CharField(
        max_length=100,
        required=False,
        label="Vehicle Model"
    )

    vehicle_type = forms.ChoiceField(
        choices=Vehicle.VEHICLE_TYPES,
        label="Vehicle Type"
    )

    service = forms.ModelChoiceField(
        queryset=WashService.objects.none(),
        label="Wash Service"
    )

    notes = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label="Notes"
    )

    def __init__(self, *args, car_wash=None, **kwargs):
        super().__init__(*args, **kwargs)

        if car_wash:
            self.fields["service"].queryset = (
                WashService.objects.filter(
                    car_wash=car_wash,
                    is_active=True
                ).order_by("name")
            )