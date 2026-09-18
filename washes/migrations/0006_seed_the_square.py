# Generated for CarWash Connect
# Seeds The Square Car Wash production configuration

from django.db import migrations
from decimal import Decimal


def seed_the_square(apps, schema_editor):

    CarWash = apps.get_model("washes", "CarWash")
    CarWashPersonnel = apps.get_model("washes", "CarWashPersonnel")
    WashService = apps.get_model("washes", "WashService")
    WashServicePrice = apps.get_model("washes", "WashServicePrice")

    # =====================================================
    # THE SQUARE CAR WASH
    # =====================================================

    car_wash, created = CarWash.objects.get_or_create(
        name="The Square Car Wash",
        defaults={
            "location": "Pretoria",
            "is_active": True,
        },
    )

    # Make sure existing record also has correct details
    car_wash.location = "Pretoria"
    car_wash.is_active = True
    car_wash.save()

    # =====================================================
    # PERSONNEL
    # =====================================================

    personnel_names = [
        "Bradley",
        "Karabo",
        "Senzo",
        "Siyabonga",
        "Sphelele",
        "Thabiso",
        "Thapelo",
    ]

    for name in personnel_names:
        personnel, created = CarWashPersonnel.objects.get_or_create(
            car_wash=car_wash,
            name=name,
            defaults={
                "role": "washer",
                "is_active": True,
            },
        )

        personnel.role = "washer"
        personnel.is_active = True
        personnel.save()

    # =====================================================
    # MAIN SERVICES
    # =====================================================

    service_data = {
        "Full Wash": {
            "small": Decimal("100.00"),
            "medium": Decimal("110.00"),
            "large": Decimal("130.00"),
            "extra_large": Decimal("150.00"),
        },

        "Wash and Dry": {
            "small": Decimal("70.00"),
            "medium": Decimal("80.00"),
            "large": Decimal("100.00"),
            "extra_large": Decimal("120.00"),
        },

        "Vacuum and Inside": {
            "small": Decimal("70.00"),
            "medium": Decimal("80.00"),
            "large": Decimal("100.00"),
            "extra_large": Decimal("120.00"),
        },

        "Wash and Hand Polish": {
            "small": Decimal("160.00"),
            "medium": Decimal("170.00"),
            "large": Decimal("190.00"),
            "extra_large": Decimal("210.00"),
        },
    }

    for service_name, prices in service_data.items():

        service, created = WashService.objects.get_or_create(
            car_wash=car_wash,
            name=service_name,
            defaults={
                "description": "",
                "price": Decimal("0.00"),
                "is_active": True,
            },
        )

        service.is_active = True
        service.save()

        for vehicle_size, price in prices.items():

            WashServicePrice.objects.update_or_create(
                service=service,
                vehicle_size=vehicle_size,
                defaults={
                    "price": price,
                },
            )

    # =====================================================
    # EXTRAS
    # =====================================================

    extras = {
        "Leather Cream": Decimal("50.00"),
        "Roof Lining": Decimal("120.00"),
        "Engine Wash": Decimal("150.00"),
    }

    for service_name, price in extras.items():

        service, created = WashService.objects.get_or_create(
            car_wash=car_wash,
            name=service_name,
            defaults={
                "description": "",
                "price": price,
                "is_active": True,
            },
        )

        service.price = price
        service.is_active = True
        service.save()


def reverse_seed_the_square(apps, schema_editor):
    """
    Intentionally left empty.

    We do not automatically delete production car wash data
    if this migration is reversed.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        (
            "washes",
            "0005_vehicle_vehicle_size_washjob_collected_at_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(
            seed_the_square,
            reverse_seed_the_square,
        ),
    ]