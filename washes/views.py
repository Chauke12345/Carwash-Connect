from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum

from .models import (
    StaffProfile,
    CarWash,
    Customer,
    Vehicle,
    WashJob,
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

    try:
        staff_profile = request.user.carwash_staff_profile

    except StaffProfile.DoesNotExist:
        return redirect("staff_login")

    # =====================================================
    # CAR WASH
    # =====================================================

    car_wash = staff_profile.car_wash

    today = timezone.localdate()

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
        .order_by("-created_at")
    )

    # =====================================================
    # ACTIVE JOBS
    # =====================================================

    active_jobs = jobs.exclude(
        status__in=[
            "collected",
            "cancelled",
        ]
    )

    # =====================================================
    # COMPLETED JOBS
    # =====================================================

    completed_jobs = jobs.filter(
        status="collected"
    )

    # =====================================================
    # PAID JOBS
    # =====================================================

    paid_jobs = jobs.filter(
        status="collected",
        payment_status="paid"
    )

    # =====================================================
    # TOTAL REVENUE
    # =====================================================

    today_revenue = (
        paid_jobs.aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    # =====================================================
    # CASH REVENUE
    # =====================================================

    cash_revenue = (
        paid_jobs
        .filter(
            payment_method="cash"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    # =====================================================
    # CARD REVENUE
    # =====================================================

    card_revenue = (
        paid_jobs
        .filter(
            payment_method="card"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    # =====================================================
    # EFT REVENUE
    # =====================================================

    eft_revenue = (
        paid_jobs
        .filter(
            payment_method="eft"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    # =====================================================
    # OTHER REVENUE
    # =====================================================

    other_revenue = (
        paid_jobs
        .filter(
            payment_method="other"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    # =====================================================
    # DASHBOARD DATA
    # =====================================================

    context = {

        "car_wash": car_wash,
        "staff_profile": staff_profile,

        "jobs": jobs,
        "active_jobs": active_jobs,
        "completed_jobs": completed_jobs,

        # Queue counts
        "registered_count": jobs.filter(
            status="registered"
        ).count(),

        "waiting_count": jobs.filter(
            status="waiting"
        ).count(),

        "washing_count": jobs.filter(
            status="washing"
        ).count(),

        "finishing_count": jobs.filter(
            status="finishing"
        ).count(),

        "ready_count": jobs.filter(
            status="ready"
        ).count(),

        "completed_count": jobs.filter(
            status="collected"
        ).count(),

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


# =========================================================
# REGISTER VEHICLE
# =========================================================

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
                form.cleaned_data[
                    "customer_name"
                ]
                .strip()
            )

            phone_number = (
                form.cleaned_data[
                    "phone_number"
                ]
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

            # Update customer name if necessary
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
                form.cleaned_data[
                    "registration_number"
                ]
                .strip()
                .upper()
            )

            vehicle_make = (
                form.cleaned_data[
                    "vehicle_make"
                ]
                .strip()
            )

            vehicle_model = (
                form.cleaned_data[
                    "vehicle_model"
                ]
                .strip()
            )

            vehicle_type = (
                form.cleaned_data[
                    "vehicle_type"
                ]
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
                    }
                )
            )

            # Update existing vehicle information
            if not vehicle_created:

                vehicle.make = vehicle_make
                vehicle.model = vehicle_model
                vehicle.vehicle_type = vehicle_type

                vehicle.save(
                    update_fields=[
                        "make",
                        "model",
                        "vehicle_type",
                    ]
                )

            # =================================================
            # CREATE NEW WASH JOB
            # =================================================

            service = form.cleaned_data[
                "service"
            ]

            WashJob.objects.create(
                car_wash=car_wash,
                customer=customer,
                vehicle=vehicle,
                service=service,
                status="waiting",
                amount=service.price,
                notes=form.cleaned_data[
                    "notes"
                ]
            )

            return redirect(
                "dashboard"
            )

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
# UPDATE WASH JOB STATUS
# =========================================================

@login_required(login_url="staff_login")
def update_job_status(request, job_id):

    try:
        staff_profile = request.user.carwash_staff_profile

    except StaffProfile.DoesNotExist:
        return redirect("staff_login")

    car_wash = staff_profile.car_wash

    # Staff can only update jobs
    # belonging to their own car wash.
    job = get_object_or_404(
        WashJob,
        id=job_id,
        car_wash=car_wash
    )

    if request.method == "POST":

        # =================================================
        # STATUS WORKFLOW
        # =================================================

        status_flow = {
            "waiting": "washing",
            "washing": "finishing",
            "finishing": "ready",
        }

        next_status = status_flow.get(
            job.status
        )

        if next_status:

            job.status = next_status

            job.save(
                update_fields=[
                    "status"
                ]
            )

    return redirect(
        "dashboard"
    )


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

    # Only READY vehicles can be paid
    # and marked as collected.
    job = get_object_or_404(
        WashJob,
        id=job_id,
        car_wash=car_wash,
        status="ready"
    )

    if request.method == "POST":

        payment_method = request.POST.get(
            "payment_method"
        )

        valid_methods = {
            "cash",
            "card",
            "eft",
            "other",
        }

        if payment_method in valid_methods:

            job.payment_method = payment_method
            job.payment_status = "paid"
            job.status = "collected"

            job.save(
                update_fields=[
                    "payment_method",
                    "payment_status",
                    "status",
                    "updated_at",
                ]
            )

    return redirect(
        "dashboard"
    )

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
    # EDVANCE TECH BILLING
    # =====================================================

    expected_invoice_revenue = (
        car_washes
        .filter(
            is_active=True
        )
        .aggregate(
            total=Sum("monthly_fee")
        )["total"] or 0
    )

    paid_invoice_revenue = (
        car_washes
        .filter(
            is_active=True,
            billing_status="paid"
        )
        .aggregate(
            total=Sum("monthly_fee")
        )["total"] or 0
    )

    outstanding_invoice_revenue = (
        car_washes
        .filter(
            is_active=True,
            billing_status__in=[
                "pending",
                "overdue",
            ]
        )
        .aggregate(
            total=Sum("monthly_fee")
        )["total"] or 0
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

        staff_count = StaffProfile.objects.filter(
            car_wash=car_wash,
            is_active=True
        ).count()

        car_wash_data.append({

            "car_wash": car_wash,

            # Operations
            "total_jobs": wash_jobs.count(),
            "active_jobs": wash_active.count(),
            "completed_jobs": wash_completed.count(),

            # Car wash business revenue
            "transaction_value": transaction_value,

            # Staff
            "staff_count": staff_count,

            # Edvance Tech billing
            "monthly_fee": car_wash.monthly_fee,
            "billing_status": car_wash.billing_status,
        })

    # =====================================================
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