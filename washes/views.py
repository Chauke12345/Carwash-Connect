from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import date

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


from .forms import VehicleRegistrationForm


# =========================================================
# HOME
# =========================================================

def home(request):
    return render(request, "washes/home.html")


# =========================================================
# STAFF LOGIN
# =========================================================

def staff_login(request):

    # If already logged in, make sure this is actually
    # a car-wash staff account before opening the dashboard.
    if request.user.is_authenticated:

        try:
            profile = request.user.carwash_staff_profile

        except StaffProfile.DoesNotExist:
            # Logged-in account is not car-wash staff.
            # Clear the session so the staff login can open.
            logout(request)
            profile = None

        if (
            profile
            and profile.is_active
            and profile.car_wash.is_active
        ):
            return redirect("dashboard")

    error = None

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            try:
                profile = user.carwash_staff_profile

            except StaffProfile.DoesNotExist:
                profile = None

            if (
                profile
                and profile.is_active
                and profile.car_wash.is_active
            ):
                login(request, user)
                return redirect("dashboard")

            error = (
                "This account is not connected "
                "to an active car wash."
            )

        else:
            error = "Invalid username or password."

    return render(
        request,
        "washes/login.html",
        {
            "error": error
        }
    )

# =========================================================
# STAFF LOGOUT
# =========================================================

def staff_logout(request):

    logout(request)

    return redirect("staff_login")


# =========================================================
# DASHBOARD
# =========================================================

@login_required(login_url="staff_login")
def dashboard(request):

    # =====================================================
    # GET LOGGED-IN STAFF PROFILE
    # =====================================================

    try:
        staff_profile = request.user.carwash_staff_profile
    except StaffProfile.DoesNotExist:
        return redirect("staff_login")

    car_wash = staff_profile.car_wash
    today = timezone.localdate()

    # =====================================================
    # ACTIVE CAR WASH PERSONNEL
    # =====================================================

    personnel = (
        CarWashPersonnel.objects
        .filter(
            car_wash=car_wash,
            is_active=True
        )
        .order_by("name")
    )

    # =====================================================
    # CAR WASH SERVICES AND SIZE PRICES
    # =====================================================

    services = (
        WashService.objects
        .filter(
            car_wash=car_wash,
            is_active=True
        )
        .prefetch_related("size_prices")
        .order_by("name")
    )

    priced_services = []
    extras = []

    # Vehicle-size columns shown on this car wash dashboard.
    if car_wash.slug == "auto-sparkles-car-wash":
        price_columns = [
            ("sedan", "Sedan"),
            ("suv", "SUV"),
            ("bakkie_s_cab", "Bakkie S/Cab"),
            ("bakkie_d_cab", "Bakkie D/Cab"),
            ("combi", "Combi"),
            ("14_seater", "14 Seater"),
            ("bigger", "Bigger"),
        ]
    else:
        price_columns = [
            ("small", "Small"),
            ("medium", "Medium"),
            ("large", "Large"),
            ("extra_large", "Extra Large"),
        ]

    for service in services:
        size_prices = {
            price.vehicle_size: price
            for price in service.size_prices.all()
        }

        if size_prices:
            display_prices = []

            for size_key, size_label in price_columns:
                service_price = size_prices.get(size_key)

                if service_price is None:
                    display_value = "—"
                elif service_price.quote_required:
                    display_value = "SQ"
                elif service_price.price is not None:
                    display_value = f"R{service_price.price:.2f}"
                else:
                    display_value = "—"

                display_prices.append({
                    "key": size_key,
                    "label": size_label,
                    "value": display_value,
                })

            priced_services.append({
                "service": service,
                "prices": display_prices,
            })
        else:
            # Services without vehicle-size prices remain extras.
            extras.append(service)

    # =====================================================
    # TODAY'S WASH JOBS
    # =====================================================

    jobs = (
        WashJob.objects
        .filter(
            car_wash=car_wash,
            created_at__date=today
        )
        .select_related(
            "customer",
            "vehicle",
            "service"
        )
        .prefetch_related(
            "assigned_personnel"
        )
        .order_by("-created_at")
    )

    # =====================================================
    # ACTIVE JOBS
    # =====================================================

    active_jobs = jobs.exclude(
        status__in=[
            "collected",
            "cancelled"
        ]
    )
        # =====================================================
    # COMPLETED / COLLECTED JOBS
    # =====================================================

    completed_jobs = (
        jobs
        .filter(status="collected")
        .order_by("-collected_at")
    )

    # =====================================================
    # PAID JOBS
    # =====================================================

    paid_jobs = jobs.filter(
        status="collected",
        payment_status="paid"
    )

  
    # =====================================================
    # TODAY'S COUNTS
    # =====================================================

    # All jobs registered today, regardless of current status
    registered_count = jobs.count()

    waiting_count = jobs.filter(
        status="waiting"
    ).count()

    washing_count = jobs.filter(
        status="washing"
    ).count()

    finishing_count = jobs.filter(
        status="finishing"
    ).count()

    ready_count = jobs.filter(
        status="ready"
    ).count()

    completed_count = jobs.filter(
        status="collected"
    ).count()

    # =====================================================
    # TODAY'S REVENUE
    # Only collected + paid jobs count as revenue
    # =====================================================

    today_revenue = (
        paid_jobs.aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    cash_revenue = (
        paid_jobs
        .filter(payment_method="cash")
        .aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    card_revenue = (
        paid_jobs
        .filter(payment_method="card")
        .aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    eft_revenue = (
        paid_jobs
        .filter(payment_method="eft")
        .aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    other_revenue = (
        paid_jobs
        .filter(payment_method="other")
        .aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    # =====================================================
    # DASHBOARD CONTEXT
    # =====================================================

    context = {

        # Car wash / logged-in staff
        "car_wash": car_wash,
        "staff_profile": staff_profile,

        # Personnel
        "personnel": personnel,

        # Services / pricing
        "priced_services": priced_services,
        "price_columns": price_columns,
        "extras": extras,

        # Jobs
        "jobs": jobs,
        "active_jobs": active_jobs,
        "completed_jobs": completed_jobs,

        # Dashboard counters
        "registered_count": registered_count,
        "waiting_count": waiting_count,
        "washing_count": washing_count,
        "finishing_count": finishing_count,
        "ready_count": ready_count,
        "completed_count": completed_count,

        # Revenue
        "today_revenue": today_revenue,
        "cash_revenue": cash_revenue,
        "card_revenue": card_revenue,
        "eft_revenue": eft_revenue,
        "other_revenue": other_revenue,
    }

    return render(
        request,
        "washes/dashboard.html",
        context
    )


@login_required(login_url="staff_login")
def register_vehicle(request):

    try:
        staff_profile = request.user.carwash_staff_profile

    except StaffProfile.DoesNotExist:
        return redirect("staff_login")

    # =====================================================
    # CAR WASH
    # =====================================================

    car_wash = staff_profile.car_wash

    # =====================================================
    # POST REQUEST
    # =====================================================

    if request.method == "POST":

        form = VehicleRegistrationForm(
            request.POST,
            car_wash=car_wash
        )

        if form.is_valid():

            # =================================================
            # CUSTOMER DETAILS
            # =================================================

            customer_name = (
                form.cleaned_data["customer_name"]
                .strip()
            )

            phone_number = (
                form.cleaned_data["phone_number"]
                .strip()
            )

            # =================================================
            # FIND OR CREATE CUSTOMER
            # =================================================

            customer, customer_created = (
                Customer.objects.get_or_create(
                    car_wash=car_wash,
                    phone_number=phone_number,
                    defaults={
                        "name": customer_name,
                    }
                )
            )

            if (
                not customer_created
                and customer.name != customer_name
            ):
                customer.name = customer_name

                customer.save(
                    update_fields=[
                        "name"
                    ]
                )

            # =================================================
            # VEHICLE DETAILS
            # =================================================

            registration_number = (
                form.cleaned_data["registration_number"]
                .strip()
                .upper()
            )

            vehicle_make = (
                form.cleaned_data["vehicle_make"]
                .strip()
            )

            vehicle_model = (
                form.cleaned_data["vehicle_model"]
                .strip()
            )

            vehicle_type = (
                form.cleaned_data["vehicle_type"]
            )

            vehicle_size = (
                form.cleaned_data["vehicle_size"]
            )

            # =================================================
            # FIND OR CREATE VEHICLE
            # =================================================

            vehicle, vehicle_created = (
                Vehicle.objects.get_or_create(
                    customer=customer,
                    registration_number=registration_number,
                    defaults={
                        "make": vehicle_make,
                        "model": vehicle_model,
                        "vehicle_type": vehicle_type,
                        "vehicle_size": vehicle_size,
                    }
                )
            )

            # =================================================
            # UPDATE EXISTING VEHICLE
            # =================================================

            if not vehicle_created:

                vehicle.make = vehicle_make
                vehicle.model = vehicle_model
                vehicle.vehicle_type = vehicle_type
                vehicle.vehicle_size = vehicle_size

                vehicle.save(
                    update_fields=[
                        "make",
                        "model",
                        "vehicle_type",
                        "vehicle_size",
                    ]
                )

            # =================================================
            # SERVICE
            # =================================================

            service = form.cleaned_data["service"]

            # =================================================
            # SIZE-BASED SERVICE PRICE
            # =================================================

            service_price = (
                WashServicePrice.objects
                .filter(
                    service=service,
                    vehicle_size=vehicle_size
                )
                .first()
            )

            has_size_pricing = (
                WashServicePrice.objects
                .filter(service=service)
                .exists()
            )

            if service_price:

                if service_price.quote_required:
                    form.add_error(
                        "service",
                        "This service requires a Special Quote (SQ) for the selected vehicle size."
                    )
                    return render(
                        request,
                        "washes/register_vehicle.html",
                        {
                            "form": form,
                            "car_wash": car_wash,
                        }
                    )

                wash_amount = service_price.price

            elif has_size_pricing:
                form.add_error(
                    "service",
                    "No price is configured for this service and vehicle size."
                )
                return render(
                    request,
                    "washes/register_vehicle.html",
                    {
                        "form": form,
                        "car_wash": car_wash,
                    }
                )

            else:
                # Compatibility for services that do not
                # have size-based pricing.
                wash_amount = service.price

            # =================================================
            # CREATE WASH JOB
            # =================================================

            WashJob.objects.create(
                car_wash=car_wash,
                customer=customer,
                vehicle=vehicle,
                service=service,
                status="waiting",
                amount=wash_amount,
                notes=form.cleaned_data["notes"]
            )

            return redirect("dashboard")

    # =====================================================
    # GET REQUEST
    # =====================================================

    else:

        form = VehicleRegistrationForm(
            car_wash=car_wash
        )

    # =====================================================
    # DISPLAY FORM
    # =====================================================

    return render(
        request,
        "washes/register_vehicle.html",
        {
            "form": form,
            "car_wash": car_wash,
        }
    )

# =========================================================
# ASSIGN PERSONNEL TO WASH JOB
# =========================================================

@login_required(login_url="staff_login")
def assign_personnel(request, job_id):

    try:
        staff_profile = request.user.carwash_staff_profile

    except StaffProfile.DoesNotExist:
        return redirect("staff_login")

    car_wash = staff_profile.car_wash

    # Security:
    # A car wash can only manage its own wash jobs.
    job = get_object_or_404(
        WashJob,
        id=job_id,
        car_wash=car_wash
    )

    if request.method == "POST":

        personnel_ids = request.POST.getlist(
            "personnel"
        )

        # Only personnel belonging to this car wash
        # may be assigned.
        selected_personnel = (
            CarWashPersonnel.objects
            .filter(
                id__in=personnel_ids,
                car_wash=car_wash,
                is_active=True
            )
        )

        job.assigned_personnel.set(
            selected_personnel
        )

    return redirect("dashboard")

# =========================================================
# UPDATE WASH JOB STATUS
# =========================================================

@login_required(login_url="staff_login")
def update_job_status(request, job_id):

    try:
        staff_profile = request.user.carwash_staff_profile
    except StaffProfile.DoesNotExist:
        return redirect("staff_login")

    car_wash = staff_profile.car_wash
    job = get_object_or_404(WashJob, id=job_id, car_wash=car_wash)

    if request.method == "POST":
        status_flow = {
            "waiting": "washing",
            "washing": "finishing",
            "finishing": "ready",
        }
        next_status = status_flow.get(job.status)

        if next_status:
            job.status = next_status
            update_fields = ["status", "updated_at"]

            if next_status == "washing" and not job.started_at:
                job.started_at = timezone.now()
                update_fields.append("started_at")

            if next_status == "ready" and not job.completed_at:
                job.completed_at = timezone.now()
                update_fields.append("completed_at")

            job.save(update_fields=update_fields)

    return redirect("dashboard")

# =========================================================
# CONFIRM PAYMENT AND COLLECT
# =========================================================

@login_required(login_url="staff_login")
def confirm_payment(request, job_id):

    try:
        staff_profile = request.user.carwash_staff_profile
    except StaffProfile.DoesNotExist:
        return redirect("staff_login")

    car_wash = staff_profile.car_wash
    job = get_object_or_404(
        WashJob,
        id=job_id,
        car_wash=car_wash,
        status="ready"
    )

    if request.method == "POST":
        payment_method = request.POST.get("payment_method")
        valid_methods = {"cash", "card", "eft", "other"}

        if payment_method in valid_methods:
            job.payment_method = payment_method
            job.payment_status = "paid"
            job.status = "collected"

            if not job.collected_at:
                job.collected_at = timezone.now()

            job.save(update_fields=[
                "payment_method",
                "payment_status",
                "status",
                "collected_at",
                "updated_at",
            ])

    return redirect("dashboard")

# =========================================================
# MANAGER DAILY REPORT
# =========================================================

@login_required(login_url="staff_login")
def daily_report(request):

    try:
        staff_profile = request.user.carwash_staff_profile

    except StaffProfile.DoesNotExist:
        return redirect("staff_login")

    # Only managers can access reports
    if staff_profile.role != "manager":
        return redirect("dashboard")

    car_wash = staff_profile.car_wash
    today = timezone.localdate()

    # =====================================================
    # TODAY'S JOBS
    # =====================================================

    jobs = (
        WashJob.objects
        .filter(
            car_wash=car_wash,
            created_at__date=today
        )
        .select_related(
            "customer",
            "vehicle",
            "service"
        )
        .order_by("-created_at")
    )

    completed_jobs = jobs.filter(
        status="collected"
    )

    active_jobs = jobs.exclude(
        status__in=[
            "collected",
            "cancelled",
        ]
    )

    paid_jobs = completed_jobs.filter(
        payment_status="paid"
    )

    # =====================================================
    # REVENUE
    # =====================================================

    total_revenue = (
        paid_jobs.aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    cash_revenue = (
        paid_jobs
        .filter(payment_method="cash")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    card_revenue = (
        paid_jobs
        .filter(payment_method="card")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    eft_revenue = (
        paid_jobs
        .filter(payment_method="eft")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    other_revenue = (
        paid_jobs
        .filter(payment_method="other")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    # =====================================================
    # REPORT DATA
    # =====================================================

    context = {
        "car_wash": car_wash,
        "staff_profile": staff_profile,
        "report_date": today,

        "jobs": jobs,
        "completed_jobs": completed_jobs,
        "active_jobs": active_jobs,

        "total_jobs": jobs.count(),
        "completed_count": completed_jobs.count(),
        "active_count": active_jobs.count(),

        "total_revenue": total_revenue,
        "cash_revenue": cash_revenue,
        "card_revenue": card_revenue,
        "eft_revenue": eft_revenue,
        "other_revenue": other_revenue,
    }

    return render(
        request,
        "washes/daily_report.html",
        context
    )
# =========================================================
# PLATFORM MONITORING
# =========================================================

@login_required(login_url="platform_login")
def platform_monitoring(request):

    # =====================================================
    # SECURITY - SUPERUSER ONLY
    # =====================================================

    if not request.user.is_superuser:
        return redirect("staff_login")

    today = timezone.localdate()

    # =====================================================
    # CAR WASHES
    # =====================================================

    car_washes = CarWash.objects.all().order_by("name")

    total_car_washes = car_washes.count()

    active_car_washes = car_washes.filter(
        is_active=True
    ).count()

        # =====================================================
    # =====================================================
    # EDVANCE TECH FIXED MONTHLY BILLING
    # =====================================================

    expected_invoice_revenue = (
        car_washes.filter(
            is_active=True
        ).aggregate(
            total=Sum("monthly_fee")
        )["total"] or 0
    )

    # PAYMENTS RECEIVED BY EDVANCE TECH THIS MONTH
    # =====================================================

    paid_invoice_revenue = (
        PlatformPayment.objects.filter(
            billing_year=today.year,
            billing_month=today.month,
        ).aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    # =====================================================
    # OUTSTANDING PLATFORM FEES
    # =====================================================

    outstanding_invoice_revenue = max(
        expected_invoice_revenue
        - paid_invoice_revenue,
        0
    )

     
    # =====================================================
    # TODAY'S JOBS ACROSS ALL CAR WASHES
    # =====================================================

    today_jobs = WashJob.objects.filter(
        created_at__date=today
    )

    active_jobs = today_jobs.exclude(
        status__in=[
            "collected",
            "cancelled",
        ]
    )

    completed_jobs = today_jobs.filter(
        status="collected"
    )

    paid_jobs = completed_jobs.filter(
        payment_status="paid"
    )


    # =====================================================
    # CAR WASH TRANSACTION VALUE
    # =====================================================

    total_transaction_value = (
        paid_jobs.aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

        # =====================================================
    # INDIVIDUAL CAR WASH DATA
    # =====================================================

    car_wash_data = []

    for car_wash in car_washes:

        # =================================================
        # TODAY'S OPERATIONS
        # =================================================

        wash_jobs = today_jobs.filter(
            car_wash=car_wash
        )

        wash_active = wash_jobs.exclude(
            status__in=[
                "collected",
                "cancelled",
            ]
        )

        wash_completed = wash_jobs.filter(
            status="collected"
        )

        wash_paid = wash_completed.filter(
            payment_status="paid"
        )

        transaction_value = (
            wash_paid.aggregate(
                total=Sum("amount")
            )["total"] or 0
        )

        # =================================================
        # MONTHLY SYSTEM USAGE
        # =================================================

        month_jobs = WashJob.objects.filter(
            car_wash=car_wash,
            created_at__year=today.year,
            created_at__month=today.month,
        )

        month_completed = month_jobs.filter(
            status="collected"
        )

        month_paid = month_completed.filter(
            payment_status="paid"
        )

        monthly_transaction_value = (
            month_paid.aggregate(
                total=Sum("amount")
            )["total"] or 0
        )

        # =================================================
        # LAST SYSTEM ACTIVITY
        # =================================================

        last_job = (
            WashJob.objects
            .filter(car_wash=car_wash)
            .order_by("-created_at")
            .first()
        )

        last_activity = (
            last_job.created_at
            if last_job
            else None
        )

        # =================================================
        # ACTIVE STAFF
        # =================================================

        staff_count = StaffProfile.objects.filter(
            car_wash=car_wash,
            is_active=True
        ).count()

        # =================================================
        # EDVANCE TECH MONTHLY BILLING
        # =================================================

        platform_fee_generated = (
            car_wash.monthly_fee
            if car_wash.is_active
            else 0
        )

        platform_fee_paid = (
            PlatformPayment.objects.filter(
                car_wash=car_wash,
                billing_year=today.year,
                billing_month=today.month,
            ).aggregate(
                total=Sum("amount")
            )["total"] or 0
        )

        platform_fee_due = max(
            platform_fee_generated
            - platform_fee_paid,
            0
        )

        # =================================================
        # DATA SENT TO PLATFORM DASHBOARD
        # =================================================

        car_wash_data.append({

            "car_wash": car_wash,

            # Today's activity
            "total_jobs": wash_jobs.count(),
            "active_jobs": wash_active.count(),
            "completed_jobs": wash_completed.count(),
            "transaction_value": transaction_value,

            # Monthly usage
            "monthly_jobs": month_jobs.count(),
            "monthly_completed_jobs": month_completed.count(),
            "monthly_transaction_value": monthly_transaction_value,

            # Last usage
            "last_activity": last_activity,

            # Staff
            "staff_count": staff_count,

            # EDVANCE TECH billing
            "monthly_fee": car_wash.monthly_fee,
            "platform_fee_generated": platform_fee_generated,
            "platform_fee_paid": platform_fee_paid,
            "platform_fee_due": platform_fee_due,
        })


    # CONTEXT
    # =====================================================

    context = {

        "report_date": today,

        # Car washes
        "total_car_washes": total_car_washes,
        "active_car_washes": active_car_washes,

        # Operations
        "total_jobs": today_jobs.count(),
        "active_jobs": active_jobs.count(),
        "completed_jobs": completed_jobs.count(),

        # Car wash transaction value
        "total_transaction_value": total_transaction_value,

        # Edvance Tech billing
        "expected_invoice_revenue": expected_invoice_revenue,
        "paid_invoice_revenue": paid_invoice_revenue,
        "outstanding_invoice_revenue": outstanding_invoice_revenue,

        # Individual businesses
        "car_wash_data": car_wash_data,
    }

    return render(
        request,
        "washes/platform_monitoring.html",
        context
    )
# =========================================================
# PLATFORM - INSPECT CAR WASH
# =========================================================

@login_required(login_url="staff_login")
def platform_car_wash_detail(request, car_wash_id):

    # Platform admins only
    if not request.user.is_superuser:
        return redirect("dashboard")

    car_wash = get_object_or_404(
        CarWash,
        id=car_wash_id
    )

    today = timezone.localdate()

    # =====================================================
    # TODAY'S JOBS
    # =====================================================

    jobs = (
        WashJob.objects
        .filter(
            car_wash=car_wash,
            created_at__date=today
        )
        .select_related(
            "customer",
            "vehicle",
            "service"
        )
        .order_by("-created_at")
    )

    active_jobs = jobs.exclude(
        status__in=[
            "collected",
            "cancelled",
        ]
    )

    completed_jobs = jobs.filter(
        status="collected"
    )

    paid_jobs = completed_jobs.filter(
        payment_status="paid"
    )

    # =====================================================
    # REVENUE
    # =====================================================

    total_revenue = (
        paid_jobs.aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    # =====================================================
    # STAFF
    # =====================================================

    staff_members = (
        StaffProfile.objects
        .filter(car_wash=car_wash)
        .select_related("user")
        .order_by("role", "user__username")
    )

    # =====================================================
    # SERVICES
    # =====================================================

    services = car_wash.services.all().order_by("name")

    # =====================================================
    # CONTEXT
    # =====================================================

    context = {
        "car_wash": car_wash,
        "report_date": today,

        "jobs": jobs,
        "active_jobs": active_jobs,
        "completed_jobs": completed_jobs,

        "total_jobs": jobs.count(),
        "active_count": active_jobs.count(),
        "completed_count": completed_jobs.count(),
        "total_revenue": total_revenue,

        "staff_members": staff_members,
        "services": services,
    }

    return render(
        request,
        "washes/platform_car_wash_detail.html",
        context
    )

# =========================================================
# PLATFORM ADMIN LOGIN
# =========================================================

def platform_login(request):

    # Already logged in as platform admin
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect("platform_monitoring")

    error = None

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        # Only superusers can use this login
        if user is not None and user.is_superuser:

            login(request, user)

            return redirect(
                "platform_monitoring"
            )

        else:

            error = (
                "Invalid platform administrator "
                "username or password."
            )

    return render(
        request,
        "washes/platform_login.html",
        {
            "error": error
        }
    )

# =========================================================
# MANAGER MONTHLY REPORT
# =========================================================

@login_required(login_url="staff_login")
def monthly_report(request):

    try:
        staff_profile = request.user.carwash_staff_profile
    except StaffProfile.DoesNotExist:
        return redirect("staff_login")

    car_wash = staff_profile.car_wash

    # Current month by default
    today = timezone.localdate()

    try:
        selected_year = int(
            request.GET.get("year", today.year)
        )
        selected_month = int(
            request.GET.get("month", today.month)
        )

        if selected_month < 1 or selected_month > 12:
            selected_month = today.month

    except (TypeError, ValueError):
        selected_year = today.year
        selected_month = today.month

    # =====================================================
    # MONTH JOBS
    # =====================================================

    month_jobs = (
        WashJob.objects
        .filter(
            car_wash=car_wash,
            created_at__year=selected_year,
            created_at__month=selected_month,
        )
        .select_related(
            "customer",
            "vehicle",
            "service"
        )
        .prefetch_related(
            "assigned_personnel"
        )
        .order_by("-created_at")
    )

    # =====================================================
    # COMPLETED / PAID JOBS
    # =====================================================

    completed_jobs = month_jobs.filter(
        status="collected"
    )

    paid_jobs = completed_jobs.filter(
        payment_status="paid"
    )

    # =====================================================
    # SUMMARY
    # =====================================================

    total_vehicles = month_jobs.count()

    completed_count = completed_jobs.count()

    total_revenue = (
        paid_jobs.aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    cash_revenue = (
        paid_jobs
        .filter(payment_method="cash")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    card_revenue = (
        paid_jobs
        .filter(payment_method="card")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    eft_revenue = (
        paid_jobs
        .filter(payment_method="eft")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    other_revenue = (
        paid_jobs
        .filter(payment_method="other")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    average_transaction = 0

    if paid_jobs.count():
        average_transaction = (
            total_revenue / paid_jobs.count()
        )

    # =====================================================
    # SERVICE BREAKDOWN
    # =====================================================

    service_breakdown = (
        completed_jobs
        .values("service__name")
        .annotate(
            total=Count("id")
        )
        .order_by("-total")
    )

    # =====================================================
    # VEHICLE SIZE BREAKDOWN
    # =====================================================

    vehicle_size_breakdown = (
        completed_jobs
        .values("vehicle__vehicle_size")
        .annotate(
            total=Count("id")
        )
        .order_by("-total")
    )

    # =====================================================
    # PERSONNEL ACTIVITY
    # =====================================================

    personnel_breakdown = (
        CarWashPersonnel.objects
        .filter(
            car_wash=car_wash,
            is_active=True
        )
        .annotate(
            completed_jobs_count=Count(
                "wash_jobs",
                filter=Q(
                    wash_jobs__car_wash=car_wash,
                    wash_jobs__status="collected",
                    wash_jobs__created_at__year=selected_year,
                    wash_jobs__created_at__month=selected_month,
                ),
                distinct=True
            )
        )
        .order_by(
            "-completed_jobs_count",
            "name"
        )
    )

    # =====================================================
    # MONTH NAME
    # =====================================================

    month_name = date(
        selected_year,
        selected_month,
        1
    ).strftime("%B %Y")

    context = {
        "car_wash": car_wash,
        "staff_profile": staff_profile,

        "selected_year": selected_year,
        "selected_month": selected_month,
        "month_name": month_name,

        "month_jobs": month_jobs,
        "completed_jobs": completed_jobs,

        "total_vehicles": total_vehicles,
        "completed_count": completed_count,

        "total_revenue": total_revenue,
        "average_transaction": average_transaction,

        "cash_revenue": cash_revenue,
        "card_revenue": card_revenue,
        "eft_revenue": eft_revenue,
        "other_revenue": other_revenue,

        "service_breakdown": service_breakdown,
        "vehicle_size_breakdown": vehicle_size_breakdown,
        "personnel_breakdown": personnel_breakdown,
    }

    return render(
        request,
        "washes/monthly_report.html",
        context
    )


