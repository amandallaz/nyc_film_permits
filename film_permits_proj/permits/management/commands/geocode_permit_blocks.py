from django.core.management import BaseCommand
import requests
from permits.models import PermitBlock
from decouple import config
# ----------------------------------------------------------------------
# Pipeline Overview (V2 PermitBlocks Geocoding)
#
# Geocoder documentation:
# https://nycplanning.github.io/Geosupport-UPG/
#
# Geocodes street blocks extracted from Permit.parking_held using the
# NYC Geoclient blockface API.
#
# To reduce API calls, geocoding is performed on unique street blocks
#
# Example:
# PermitBlock rows
#     ↓
# identify unique block combinations
#     (on_street, cross_street_one, cross_street_two, borough)
#     ↓
# geocode each unique block once using NYC Geoclient
#     ↓
# compute midpoint of the two bounding intersections
#     ↓
# update all matching PermitBlock rows with the same coordinates
#
# reduces the geocoding workload:
# PermitBlock rows: ~54k
# Unique blocks:    ~17k
#
# ----------------------------------------------------------------------

SUBSCRIPTION_KEY = config("SUBSCRIPTION_KEY")

def geocode_blockface(on_street, cross1, cross2, borough):
    """
    Geocode street block using the NYC Geoclient blockface endpoint.
    Returns midpoint of the two intersections.
    """

    url = "https://api.nyc.gov/geoclient/v2/blockface.json"

    params = {
        "onStreet": on_street,
        "crossStreetOne": cross1,
        "crossStreetTwo": cross2,
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

            lat = (lat1 + lat2) / 2
            lon = (lon1 + lon2) / 2

            return lat, lon

    except Exception:
        return None, None

    return None, None


class Command(BaseCommand):

    help = "Geocode unique PermitBlock street segments using NYC Geoclient"

    def handle(self, *args, **options):

        blocks = (
            PermitBlock.objects
            .filter(lat__isnull=True)
            .values(
                "on_street",
                "cross_street_one",
                "cross_street_two",
                "borough"
            )
            .distinct()
        )

        total_blocks = blocks.count()

        success_count = 0
        failure_count = 0
        rows_updated = 0

        for idx, block in enumerate(blocks, start=1):

            on_street = block["on_street"]
            cross1 = block["cross_street_one"]
            cross2 = block["cross_street_two"]
            borough = block["borough"]

            lat, lon = geocode_blockface(on_street, cross1, cross2, borough)

            if lat and lon:

                updated = (
                    PermitBlock.objects.filter(
                        on_street=on_street,
                        cross_street_one=cross1,
                        cross_street_two=cross2,
                        borough=borough,
                    )
                    .update(lat=lat, lon=lon, geocode_status="success")
                )

                rows_updated += updated
                success_count += 1

                self.stdout.write(f"[{idx}/{total_blocks}] ✅ Geocoded")

            else:

                PermitBlock.objects.filter(
                    on_street=on_street,
                    cross_street_one=cross1,
                    cross_street_two=cross2,
                    borough=borough,
                ).update(geocode_status="failed")

                failure_count += 1

                self.stdout.write(f"[{idx}/{total_blocks}] ❌ Failed")

        self.stdout.write(f"Unique blocks queued: {total_blocks}")
        self.stdout.write(f"Successfully geocoded: {success_count}")
        self.stdout.write(f"Failures: {failure_count}")
        self.stdout.write(f"PermitBlock rows updated: {rows_updated}")