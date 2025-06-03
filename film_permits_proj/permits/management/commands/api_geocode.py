from django.core.management import BaseCommand
import requests
from permits.models import Permit

SUBSCRIPTION_KEY = "17b2724cb1464fb59ead312fe97c4b04"

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
    
    response = requests.get(url, params=params, headers=headers)
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
        # print(type(Permit)) returns <class 'django.db.models.base.ModelBase'>
        for i in Permit.objects.all(): # .objects.all(): makes it iterable # limit 5 [:5]:
            text = i.parking_held.split(",")[0]
            borough = i.borough
            event_id = i.event_id
            # print(text, borough, event_id)
            # print("-----")

            on_street, cross1, cross2 = parse_blockface(text)
            lat, lon = geocode_blockface(on_street, cross1, cross2, borough)
            # print(i, event_id, lat, lon)
            # print("----") # example i: 836995 - Shooting Permit

            # i.id how to update record in model (objects update) 
            if lat and lon:
                i.lat = lat
                i.lon = lon
                i.save()

            # update to have better logging??
            # if lat and lon:
            #     i.lat = lat
            #     i.lon = lon
            #     i.save()
            #     self.stdout.write(f"[{idx}/{total}] ✅ Updated {event_id} → ({lat:.5f}, {lon:.5f})")
            # else:
            #     self.stdout.write(f"[{idx}/{total}] ❌ Failed to geocode {event_id}")







