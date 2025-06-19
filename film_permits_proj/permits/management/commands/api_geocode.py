from django.core.management import BaseCommand
import requests
from permits.models import Permit
from decouple import config

SUBSCRIPTION_KEY = config('SUBSCRIPTION_KEY')

# parse address string to match geoclient api formatting
def parse_blockface(text):
    try:
        parts = text.split(" between ")
        on_street = parts[0].strip()
        cross1, cross2 = parts[1].split(" and ")
        return on_street, cross1.strip(), cross2.strip()
        # print("on_street", on_street, "cross1", cross1.strip(), "cross2", cross2.strip())
    except Exception:
        return None, None, None

# send address parameters to geoclient api for blockface matching, return lat and lon coordinates 
def geocode_blockface(on_street, cross_street_one, cross_street_two, borough):
    url = "https://api.nyc.gov/geoclient/v2/blockface.json"
    params = {
        "onStreet": on_street,
        "crossStreetOne": cross_street_one,
        "crossStreetTwo": cross_street_two,
        "borough": borough
    }
    headers = {
        "Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY }
    
    response = requests.get(url, params=params, headers=headers, timeout=5)
    try:
        data = response.json()['blockface']
        if data.get("geosupportReturnCode") == "00":
            lat1 = float(data['latitudeOfFromIntersection'])
            lon1 = float(data['longitudeOfFromIntersection'])
            lat2 = float(data['latitudeOfToIntersection'])
            lon2 = float(data['longitudeOfToIntersection'])
            return (lat1 + lat2) / 2, (lon1 + lon2) / 2
    except Exception:
        return None, None
    return None, None

class Command(BaseCommand):
    def handle(self, *args, **options):
        # total = Permit.objects.count()
        # print(type(Permit)) returns <class 'django.db.models.base.ModelBase'>
        qs = Permit.objects.filter(lat__isnull=True, lon__isnull=True)
        total = qs.count()

        # for idx, i in enumerate(Permit.objects.all(), start=1): #.objects.all(): makes it iterable #limit 5 [:5]:
        for idx, i in enumerate(qs, start=1):
            text = i.parking_held.split(",")[0]
            borough = i.borough
            event_id = i.event_id
            # print(text, borough, event_id)
            # print("-----")

            on_street, cross1, cross2 = parse_blockface(text)
            lat, lon = geocode_blockface(on_street, cross1, cross2, borough)
            # print(i, event_id, lat, lon)
            # print("----") # example i: 836995 - Shooting Permit

            # update record in model
            if lat and lon:
                i.lat = lat
                i.lon = lon
                i.save()
                self.stdout.write(f"[{idx}/{total}] ✅ Updated")
            else:
                self.stdout.write(f"[{idx}/{total}] ❌ Failed to geocode {event_id}")







