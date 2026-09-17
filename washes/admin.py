from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import (
    CarWash,
    StaffProfile,
    WashService,
    Customer,
    Vehicle,
    WashJob,
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
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
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
# =========================================================

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "car_wash",
        "role",
        "is_active",
    )

    list_filter = (
        "car_wash",
        "role",
        "is_active",
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
    )

    search_fields = (
        "registration_number",
        "customer__name",
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
    )

    search_fields = (
        "vehicle__registration_number",
        "customer__name",
        "customer__phone_number",
    )