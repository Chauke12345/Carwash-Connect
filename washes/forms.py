from django import forms

from .models import WashService, Vehicle


# =========================================================
# VEHICLE REGISTRATION FORM
# =========================================================

class VehicleRegistrationForm(forms.Form):

    # =====================================================
    # CUSTOMER
    # =====================================================

    customer_name = forms.CharField(
        max_length=150,
        label="Customer Name",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Customer name",
                "autocomplete": "name",
            }
        )
    )

    phone_number = forms.CharField(
        max_length=20,
        label="Phone Number",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Phone number",
                "autocomplete": "tel",
            }
        )
    )

    # =====================================================
    # VEHICLE
    # =====================================================

    registration_number = forms.CharField(
        max_length=30,
        label="Vehicle Registration",
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g. ABC 123 GP",
                "autocomplete": "off",
            }
        )
    )

    vehicle_make = forms.CharField(
        max_length=100,
        required=False,
        label="Vehicle Make",
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g. Toyota"
            }
        )
    )

    vehicle_model = forms.CharField(
        max_length=100,
        required=False,
        label="Vehicle Model",
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g. Corolla"
            }
        )
    )

    vehicle_type = forms.ChoiceField(
        choices=Vehicle.VEHICLE_TYPES,
        label="Vehicle Type"
    )

    # =====================================================
    # VEHICLE SIZE
    # Determines the correct size-based wash price.
    # =====================================================

    vehicle_size = forms.ChoiceField(
        choices=Vehicle.VEHICLE_SIZE_CHOICES,
        label="Vehicle Size"
    )

    # =====================================================
    # WASH SERVICE
    # =====================================================

    service = forms.ModelChoiceField(
        queryset=WashService.objects.none(),
        label="Wash Service",
        empty_label="Select wash service"
    )

    # =====================================================
    # NOTES
    # =====================================================

    notes = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Optional notes"
            }
        ),
        required=False,
        label="Notes"
    )

    # =====================================================
    # INITIALISE FORM
    # =====================================================

    def __init__(self, *args, car_wash=None, **kwargs):

        super().__init__(*args, **kwargs)

        # Only show services belonging to the
        # currently logged-in car wash.
        if car_wash:

            # Vehicle-size options are specific to each car wash.
            # Auto Sparkles uses the categories from its own price board.
            if car_wash.slug == "auto-sparkles-car-wash":
                self.fields["vehicle_size"].choices = [
                    ("sedan", "Sedan"),
                    ("suv", "SUV"),
                    ("bakkie_s_cab", "Bakkie S/Cab"),
                    ("bakkie_d_cab", "Bakkie D/Cab"),
                    ("combi", "Combi"),
                    ("14_seater", "14 Seater"),
                    ("bigger", "Bigger"),
                ]
            elif car_wash.slug == "iscars-autowash":
                self.fields["vehicle_size"].choices = [
                    ("sedan", "Sedan / Hatch"),
                    ("mini_suv", "Mini SUV"),
                    ("suv", "SUV"),
                    ("mpv", "MPV"),
                    ("taxi", "Taxi"),
                    ("bike", "Bike"),
                    ("trailer", "Trailer"),
                ]

            else:
                # Keep the existing categories for all other car washes.
                self.fields["vehicle_size"].choices = [
                    ("small", "Small"),
                    ("medium", "Medium"),
                    ("large", "Large"),
                    ("extra_large", "Extra Large"),
                ]

            self.fields["service"].queryset = (
                WashService.objects
                .filter(
                    car_wash=car_wash,
                    is_active=True
                )
                .order_by("name")
            )
