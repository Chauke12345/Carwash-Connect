from django.urls import path
from . import views


urlpatterns = [
    path("", views.home, name="home"),

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

    path(
        "dashboard/",
        views.dashboard,
        name="dashboard"
    ),

    path(
        "register-vehicle/",
        views.register_vehicle,
        name="register_vehicle"
    ),

    path(
        "job/<int:job_id>/update-status/",
        views.update_job_status,
        name="update_job_status"
    ),

    path(
        "job/<int:job_id>/payment/",
        views.confirm_payment,
        name="confirm_payment"
    ),

    path(
    "reports/daily/",
    views.daily_report,
    name="daily_report"
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

path(
    "platform/login/",
    views.platform_login,
    name="platform_login"
),
]