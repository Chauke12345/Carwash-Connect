from django.contrib import admin

from .models import (
    CarWash,
    StaffProfile,
    CarWashPersonnel,
    Customer,
    Vehicle,
    WashService,
    WashServicePrice,
    WashJob,
    PlatformPayment,
)


# =========================================================
# CAR WASHES
# =========================================================

@admin.register(CarWash)
class CarWashAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "location",
        "owner_name",
        "phone_number",
        "monthly_fee",
        "billing_status",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "billing_status",
        "location",
    )

    search_fields = (
        "name",
        "owner_name",
        "phone_number",
        "location",
    )

    prepopulated_fields = {
        "slug": ("name",)
    }


# =========================================================
# STAFF
# People who log into CarWash Connect
# =========================================================

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "car_wash",
        "role",
        "phone_number",
        "is_active",
    )

    list_filter = (
        "car_wash",
        "role",
        "is_active",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "phone_number",
        "car_wash__name",
    )


# =========================================================
# CAR WASH PERSONNEL
# People physically working on vehicles
# =========================================================

@admin.register(CarWashPersonnel)
class CarWashPersonnelAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "car_wash",
        "role",
        "phone_number",
        "is_active",
        "created_at",
    )

    list_filter = (
        "car_wash",
        "role",
        "is_active",
    )

    search_fields = (
        "name",
        "phone_number",
        "car_wash__name",
    )

    ordering = (
        "car_wash",
        "name",
    )


# =========================================================
# SERVICE PRICE INLINE
# Allows Small / Medium / Large / Extra Large prices
# to be entered directly inside a service.
# =========================================================

class WashServicePriceInline(admin.TabularInline):

    model = WashServicePrice

    extra = 0

    fields = (
        "vehicle_size",
        "price",
    )


# =========================================================
# SERVICES
# =========================================================

@admin.register(WashService)
class WashServiceAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "car_wash",
        "price",
        "is_active",
    )

    list_filter = (
        "car_wash",
        "is_active",
    )

    search_fields = (
        "name",
        "car_wash__name",
    )

    inlines = [
        WashServicePriceInline
    ]


# =========================================================
# SERVICE PRICES
# =========================================================

@admin.register(WashServicePrice)
class WashServicePriceAdmin(admin.ModelAdmin):

    list_display = (
        "service",
        "vehicle_size",
        "price",
        "car_wash_name",
    )

    list_filter = (
        "vehicle_size",
        "service__car_wash",
    )

    search_fields = (
        "service__name",
        "service__car_wash__name",
    )

    @admin.display(description="Car Wash")
    def car_wash_name(self, obj):
        return obj.service.car_wash.name


# =========================================================
# CUSTOMERS
# =========================================================

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "phone_number",
        "car_wash",
        "created_at",
    )

    list_filter = (
        "car_wash",
    )

    search_fields = (
        "name",
        "phone_number",
        "car_wash__name",
    )


# =========================================================
# VEHICLES
# =========================================================

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):

    list_display = (
        "registration_number",
        "customer",
        "make",
        "model",
        "vehicle_type",
        "vehicle_size",
    )

    list_filter = (
        "vehicle_type",
        "vehicle_size",
    )

    search_fields = (
        "registration_number",
        "customer__name",
        "make",
        "model",
    )


# =========================================================
# WASH JOBS
# =========================================================

@admin.register(WashJob)
class WashJobAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "car_wash",
        "vehicle",
        "service",
        "personnel_names",
        "status",
        "amount",
        "payment_status",
        "created_at",
    )

    list_filter = (
        "car_wash",
        "status",
        "payment_status",
        "payment_method",
        "assigned_personnel",
    )

    search_fields = (
        "vehicle__registration_number",
        "customer__name",
        "customer__phone_number",
        "assigned_personnel__name",
    )

    filter_horizontal = (
        "assigned_personnel",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    @admin.display(description="Assigned Personnel")
    def personnel_names(self, obj):

        personnel = obj.assigned_personnel.all()

        if not personnel:
            return "Not assigned"

        return ", ".join(
            person.name
            for person in personnel
        )


# =========================================================
# PLATFORM PAYMENT ADMIN
# Payments made by car washes to Edvance Tech
# =========================================================

@admin.register(PlatformPayment)
class PlatformPaymentAdmin(admin.ModelAdmin):

    list_display = (
        "car_wash",
        "amount",
        "billing_month",
        "billing_year",
        "payment_method",
        "reference",
        "paid_at",
    )

    list_filter = (
        "billing_year",
        "billing_month",
        "payment_method",
        "car_wash",
    )

    search_fields = (
        "car_wash__name",
        "reference",
    )

    readonly_fields = (
        "paid_at",
    )

    ordering = (
        "-billing_year",
        "-billing_month",
        "-paid_at",
    )