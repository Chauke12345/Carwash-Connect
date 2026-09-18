from django.db import models
from django.contrib.auth.models import User


# =========================================================
# CAR WASH
# =========================================================

class CarWash(models.Model):

    BILLING_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
    ]

    name = models.CharField(max_length=150)

    slug = models.SlugField(unique=True)

    owner_name = models.CharField(max_length=150)

    phone_number = models.CharField(max_length=20)

    whatsapp_number = models.CharField(
        max_length=20,
        blank=True
    )

    email = models.EmailField(blank=True)

    address = models.TextField(blank=True)

    location = models.CharField(max_length=150)

    is_active = models.BooleanField(default=True)

    # =====================================================
    # BILLING
    # =====================================================

    monthly_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=500.00
    )

    billing_status = models.CharField(
        max_length=20,
        choices=BILLING_STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Car wash"
        verbose_name_plural = "Car washes"

    def __str__(self):
        return self.name


# =========================================================
# STAFF PROFILE
# People who LOGIN to CarWash Connect
# =========================================================

class StaffProfile(models.Model):

    ROLE_CHOICES = [
        ("manager", "Manager"),
        ("staff", "Staff"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="carwash_staff_profile"
    )

    car_wash = models.ForeignKey(
        CarWash,
        on_delete=models.CASCADE,
        related_name="staff_members"
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="staff"
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.car_wash.name}"


# =========================================================
# CAR WASH PERSONNEL
# People physically working on vehicles
# No login account required
# =========================================================

class CarWashPersonnel(models.Model):

    ROLE_CHOICES = [
        ("washer", "Washer"),
        ("interior", "Interior Cleaner"),
        ("dryer", "Dryer / Finisher"),
        ("polisher", "Polisher"),
        ("supervisor", "Supervisor"),
        ("cashier", "Cashier"),
        ("other", "Other"),
    ]

    car_wash = models.ForeignKey(
        CarWash,
        on_delete=models.CASCADE,
        related_name="personnel"
    )

    name = models.CharField(
        max_length=150
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True
    )

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default="washer"
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Car wash personnel"
        verbose_name_plural = "Car wash personnel"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} - {self.car_wash.name}"


# =========================================================
# SERVICES
# =========================================================

class WashService(models.Model):

    car_wash = models.ForeignKey(
        CarWash,
        on_delete=models.CASCADE,
        related_name="services"
    )

    name = models.CharField(
        max_length=100
    )

    description = models.TextField(
        blank=True
    )

    # Keep this for compatibility with your existing system.
    # Vehicle-size pricing can override it.
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.name} - {self.car_wash.name}"


# =========================================================
# SERVICE PRICE BY VEHICLE SIZE
# Example:
# Full Wash + Small = R100
# Full Wash + Medium = R110
# =========================================================

class WashServicePrice(models.Model):

    VEHICLE_SIZE_CHOICES = [
        ("small", "Small"),
        ("medium", "Medium"),
        ("large", "Large"),
        ("extra_large", "Extra Large"),
    ]

    service = models.ForeignKey(
        WashService,
        on_delete=models.CASCADE,
        related_name="size_prices"
    )

    vehicle_size = models.CharField(
        max_length=20,
        choices=VEHICLE_SIZE_CHOICES
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    class Meta:
        unique_together = (
            "service",
            "vehicle_size"
        )

        ordering = [
            "service",
            "vehicle_size"
        ]

    def __str__(self):
        return (
            f"{self.service.name} - "
            f"{self.get_vehicle_size_display()} - "
            f"R{self.price}"
        )


# =========================================================
# CUSTOMER
# =========================================================

class Customer(models.Model):

    car_wash = models.ForeignKey(
        CarWash,
        on_delete=models.CASCADE,
        related_name="customers"
    )

    name = models.CharField(
        max_length=150
    )

    phone_number = models.CharField(
        max_length=20
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # =====================================================
    # WHATSAPP NUMBER
    # =====================================================

    @property
    def whatsapp_number(self):

        number = (
            self.phone_number
            .strip()
            .replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
            .replace("+", "")
        )

        if number.startswith("0"):
            number = "27" + number[1:]

        return number

    def __str__(self):
        return self.name


# =========================================================
# VEHICLE
# =========================================================

class Vehicle(models.Model):

    VEHICLE_TYPES = [
        ("sedan", "Sedan"),
        ("hatchback", "Hatchback"),
        ("suv", "SUV"),
        ("bakkie", "Bakkie"),
        ("minibus", "Minibus / Taxi"),
        ("other", "Other"),
    ]

    VEHICLE_SIZE_CHOICES = [
        ("small", "Small"),
        ("medium", "Medium"),
        ("large", "Large"),
        ("extra_large", "Extra Large"),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="vehicles"
    )

    registration_number = models.CharField(
        max_length=30
    )

    make = models.CharField(
        max_length=100,
        blank=True
    )

    model = models.CharField(
        max_length=100,
        blank=True
    )

    vehicle_type = models.CharField(
        max_length=20,
        choices=VEHICLE_TYPES,
        default="sedan"
    )

    vehicle_size = models.CharField(
        max_length=20,
        choices=VEHICLE_SIZE_CHOICES,
        default="medium"
    )

    def __str__(self):
        return self.registration_number


# =========================================================
# WASH JOB
# =========================================================

class WashJob(models.Model):

    STATUS_CHOICES = [
        ("registered", "Registered"),
        ("waiting", "Waiting"),
        ("washing", "Washing"),
        ("finishing", "Drying / Finishing"),
        ("ready", "Ready"),
        ("collected", "Collected"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Payment Pending"),
        ("paid", "Paid"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("cash", "Cash"),
        ("card", "Card"),
        ("eft", "EFT"),
        ("other", "Other"),
    ]

    car_wash = models.ForeignKey(
        CarWash,
        on_delete=models.CASCADE,
        related_name="wash_jobs"
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="wash_jobs"
    )

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.PROTECT,
        related_name="wash_jobs"
    )

    service = models.ForeignKey(
        WashService,
        on_delete=models.PROTECT,
        related_name="wash_jobs"
    )

    # =====================================================
    # PERSONNEL ASSIGNMENT
    # Multiple workers can work on one vehicle
    # =====================================================

    assigned_personnel = models.ManyToManyField(
        CarWashPersonnel,
        related_name="wash_jobs",
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="registered"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending"
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True
    )

    notes = models.TextField(
        blank=True
    )

    # =====================================================
    # WORKFLOW TIMES
    # Useful for reports and performance
    # =====================================================

    started_at = models.DateTimeField(
        null=True,
        blank=True
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    collected_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return (
            f"Wash #{self.id} - "
            f"{self.vehicle.registration_number}"
        )


# =========================================================
# PLATFORM PAYMENT
# Payments made by car washes to Edvance Tech
# =========================================================

class PlatformPayment(models.Model):

    PAYMENT_METHOD_CHOICES = [
        ("eft", "EFT"),
        ("cash", "Cash"),
        ("card", "Card"),
        ("other", "Other"),
    ]

    car_wash = models.ForeignKey(
        CarWash,
        on_delete=models.CASCADE,
        related_name="platform_payments"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    billing_year = models.PositiveIntegerField()

    billing_month = models.PositiveSmallIntegerField()

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default="eft"
    )

    reference = models.CharField(
        max_length=100,
        blank=True
    )

    notes = models.TextField(
        blank=True
    )

    paid_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.car_wash.name} - "
            f"{self.billing_year}/{self.billing_month} - "
            f"R{self.amount}"
        )