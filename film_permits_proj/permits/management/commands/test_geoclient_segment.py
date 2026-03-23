from django.core.management.base import BaseCommand
from decouple import config
import requests
import json


SUBSCRIPTION_KEY = config("SUBSCRIPTION_KEY")


class Command(BaseCommand):
    help = "Test Geoclient blockface response fields"

    def handle(self, *args, **options):
        url = "https://api.nyc.gov/geoclient/v2/blockface.json"

        params = {
            "onStreet": "MONITOR STREET",
            "crossStreetOne": "GREENPOINT AVENUE",
            "crossStreetTwo": "NORMAN AVENUE",
            "borough": "Brooklyn",
        }

        headers = {
            "Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        print(json.dumps(data, indent=2))