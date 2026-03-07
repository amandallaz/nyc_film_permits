from django.core.management import BaseCommand
import requests
from permits.models import Permit
from decouple import config

# ----------------------------------------------------------------------
# Pipeline Overview (V1 First String Geocoding)
#
# Geocoder documentation:
# https://nycplanning.github.io/Geosupport-UPG/
# 
# Converts Permit.parking_held street block strings into approximate
# permit locations using the NYC Geoclient blockface API, Function 3
#
# Many permits contain multiple street blocks. For this V1 approach,
# only the first listed block is geocoded, producing one approximate
# location per permit.
#
# Steps:
#
# Permit.parking_held
#     ↓
# select first listed street block (comma-separated)
#     ↓
# normalize whitespace
#     ↓
# parse blockface:
#     "ON_STREET between CROSS1 and CROSS2"
#     ↓
# geocode blockface using NYC Geoclient API
#     ↓
# compute midpoint of bounding intersections
#     ↓
# store coordinates on Permit.lat / Permit.lon
# ----------------------------------------------------------------------

SUBSCRIPTION_KEY = config("SUBSCRIPTION_KEY")

def normalize_whitespace(text):
    """Collapse repeated internal whitespace into single spaces."""
    return " ".join(text.split())


def parse_blockface(text):
    """
    Parse a blockface string of the form:
    'ON_STREET between CROSS1 and CROSS2'
    """
    try:
        cleaned = normalize_whitespace(text)
        parts = cleaned.split(" between ")
        on_street = parts[0].strip()
        cross1, cross2 = parts[1].split(" and ")
        return on_street, cross1.strip(), cross2.strip()
    except Exception:
        return None, None, None


def geocode_blockface(on_street, cross_street_one, cross_street_two, borough):
    """
    Geocode a street segment using the NYC Geoclient blockface endpoint.
    Returns the midpoint of the two bounding intersections.
    """
    url = "https://api.nyc.gov/geoclient/v2/blockface.json"
    params = {
        "onStreet": on_street,
        "crossStreetOne": cross_street_one,
        "crossStreetTwo": cross_street_two,
        "borough": borough,
    }
    headers = {"Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()["blockface"]
    except Exception:
        return None, None

    try:
        if data.get("geosupportReturnCode") == "00":
            lat1 = float(data["latitudeOfFromIntersection"])
            lon1 = float(data["longitudeOfFromIntersection"])
            lat2 = float(data["latitudeOfToIntersection"])
            lon2 = float(data["longitudeOfToIntersection"])
            return (lat1 + lat2) / 2, (lon1 + lon2) / 2
    except Exception:
        return None, None

    return None, None


class Command(BaseCommand):
    help = "Geocode permit locations using the first block listed in parking_held"
    def handle(self, *args, **options):
        qs = Permit.objects.filter(lat__isnull=True, lon__isnull=True)
        total = qs.count()

        success_count = 0
        parse_fail_count = 0
        geocode_fail_count = 0

        for idx, permit in enumerate(qs, start=1):
            # [0], first listed segment is geocoded.
            text = permit.parking_held.split(",")[0]
            borough = permit.borough
            event_id = permit.event_id

            on_street, cross1, cross2 = parse_blockface(text)

            if not all([on_street, cross1, cross2]):
                parse_fail_count += 1
                self.stdout.write(f"[{idx}/{total}] ❌ Parse failed for {event_id}")
                continue

            lat, lon = geocode_blockface(on_street, cross1, cross2, borough)

            if lat and lon:
                permit.lat = lat
                permit.lon = lon
                permit.save()
                success_count += 1
                self.stdout.write(f"[{idx}/{total}] ✅ Updated")
            else:
                geocode_fail_count += 1
                self.stdout.write(f"[{idx}/{total}] ❌ Failed to geocode {event_id}")

        self.stdout.write(f"Total permits queued: {total}")
        self.stdout.write(f"Successfully geocoded: {success_count}")
        self.stdout.write(f"Parse failures: {parse_fail_count}")
        self.stdout.write(f"Geocode failures: {geocode_fail_count}")







