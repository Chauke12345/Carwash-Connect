from django.urls import path
from . import views


urlpatterns = [

    # =====================================================
    # HOME
    # =====================================================

    path(
        "",
        views.home,
        name="home"
    ),

    # =====================================================
    # STAFF AUTHENTICATION
    # =====================================================

    path(
        "login/",
        views.staff_login,
        name="staff_login"
    ),

    path(
        "logout/",
        views.staff_logout,
        name="staff_logout"
    ),

    # =====================================================
    # CAR WASH DASHBOARD
    # =====================================================

    path(
        "dashboard/",
        views.dashboard,
        name="dashboard"
    ),

    # =====================================================
    # VEHICLE REGISTRATION
    # =====================================================

    path(
        "register-vehicle/",
        views.register_vehicle,
        name="register_vehicle"
    ),

    # =====================================================
    # RETURNING VEHICLE LOOKUP
    # =====================================================

    path(
        "vehicle-lookup/",
        views.vehicle_lookup,
        name="vehicle_lookup"
    ),

    # =====================================================
    # WASH JOB - ASSIGN PERSONNEL
    # =====================================================

    path(
        "job/<int:job_id>/assign-personnel/",
        views.assign_personnel,
        name="assign_personnel"
    ),

    # =====================================================
    # WASH JOB - UPDATE STATUS
    # =====================================================

    path(
        "job/<int:job_id>/update-status/",
        views.update_job_status,
        name="update_job_status"
    ),

    # =====================================================
    # WASH JOB - PAYMENT
    # =====================================================

    path(
        "job/<int:job_id>/payment/",
        views.confirm_payment,
        name="confirm_payment"
    ),

    # =====================================================
    # MANAGER REPORTS
    # =====================================================

    path(
        "reports/daily/",
        views.daily_report,
        name="daily_report"
    ),

    path(
        "reports/monthly/",
        views.monthly_report,
        name="monthly_report"
    ),

    # =====================================================
    # EDVANCE TECH PLATFORM
    # =====================================================

    path(
        "platform/login/",
        views.platform_login,
        name="platform_login"
    ),

    path(
        "platform/monitoring/",
        views.platform_monitoring,
        name="platform_monitoring"
    ),

    path(
        "platform/car-wash/<int:car_wash_id>/",
        views.platform_car_wash_detail,
        name="platform_car_wash_detail"
    ),
]