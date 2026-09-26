from decimal import Decimal
from django.db import transaction
from washes.models import CarWash, WashService, WashServicePrice

car_wash = CarWash.objects.get(slug="iscars-autowash")

# Prices supplied by Iscars AutoWash.
# None = that service is not offered/listed for that vehicle type.
menu = {
    "Wash and Go": {
        "sedan": 50, "mini_suv": 60, "suv": 70,
        "mpv": 100, "taxi": 100,
    },
    "Wash and Dry": {
        "sedan": 80, "mini_suv": 90, "suv": 100,
        "mpv": 120, "taxi": 120,
    },
    "Full House": {
        "sedan": 120, "mini_suv": 130, "suv": 150,
        "mpv": 180, "taxi": 200,
    },
    "Full House Combo with Dash Shine": {
        "sedan": 150, "mini_suv": 150, "suv": 170,
    },
    "Full House + Polish": {
        "sedan": 270, "mini_suv": 300,
    },
    "Hand Polish Add-on": {
        "sedan": 150, "mini_suv": 170, "suv": 170,
    },
    "Ceramic Instant Detail Add-on": {
        "sedan": 100, "mini_suv": 120, "suv": 120,
    },
    "Engine Wash": {
        "sedan": 80, "mini_suv": 90, "suv": 100,
    },
    "Under Carriage": {
        "sedan": 50, "mini_suv": 60, "suv": 70,
    },
    "Plastic Polish Add-on": {
        "sedan": 20, "mini_suv": 30, "suv": 40,
    },
    "Leather Treatment Add-on": {
        "sedan": 80, "mini_suv": 100, "suv": 90,
    },
    "Carpet Shine Add-on": {
        "sedan": 20, "mini_suv": 30, "suv": 40,
    },
    "Inside Clean Only": {
        "sedan": 60, "mini_suv": 70, "suv": 80,
    },
    "Bike Wash": {
        "bike": 70,
    },
    "Trailer Wash": {
        "trailer": 100,
    },
}

# Variable-price services.
quote_services = {
    "Valet": ["sedan", "mini_suv", "suv"],
    "Apply Own Polish": ["sedan"],
}

with transaction.atomic():

    for service_name, prices in menu.items():

        service, _ = WashService.objects.get_or_create(
            car_wash=car_wash,
            name=service_name,
            defaults={
                "price": Decimal("0.00"),
                "is_active": True,
            },
        )

        service.is_active = True
        service.save(update_fields=["is_active"])

        for vehicle_size, amount in prices.items():

            WashServicePrice.objects.update_or_create(
                service=service,
                vehicle_size=vehicle_size,
                defaults={
                    "price": Decimal(str(amount)),
                    "quote_required": False,
                },
            )

    for service_name, vehicle_sizes in quote_services.items():

        service, _ = WashService.objects.get_or_create(
            car_wash=car_wash,
            name=service_name,
            defaults={
                "price": Decimal("0.00"),
                "is_active": True,
            },
        )

        service.is_active = True
        service.save(update_fields=["is_active"])

        for vehicle_size in vehicle_sizes:

            WashServicePrice.objects.update_or_create(
                service=service,
                vehicle_size=vehicle_size,
                defaults={
                    "price": None,
                    "quote_required": True,
                },
            )

print("SUCCESS: Iscars AutoWash menu loaded locally")
print("Services:", WashService.objects.filter(car_wash=car_wash, is_active=True).count())
print("Size prices:", WashServicePrice.objects.filter(service__car_wash=car_wash).count())
