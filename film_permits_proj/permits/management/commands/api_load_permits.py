from django.core.management import BaseCommand
import requests
from django.utils.dateparse import parse_datetime
from permits.models import Permit

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        url = "https://data.cityofnewyork.us/resource/tg4x-b46p.json"
        # no API key needed

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            self.stderr.write(f"API request failed: {e}")
            return

        created_count = 0

        for entry in data:
            try:
                event_id = entry.get("eventid")
                event_type = entry.get("eventtype")
                start_datetime = parse_datetime(entry.get("startdatetime"))
                end_datetime = parse_datetime(entry.get("enddatetime"))
                parking_held = entry.get("parkingheld", "")
                borough = entry.get("borough", "")
                community_boards = entry.get("communityboard_s", "")
                category = entry.get("category", "")
                subcategory = entry.get("subcategoryname", "")
                zip_codes = entry.get("zipcode_s", "")

                obj, created = Permit.objects.update_or_create(
                    event_id=event_id,
                    event_type = event_type,
                    start_datetime = start_datetime,
                    end_datetime = end_datetime,
                    parking_held = parking_held,
                    borough = borough,
                    community_boards = community_boards,
                    category = category,
                    subcategory = subcategory,
                    zip_codes = zip_codes,
                    lat = None,
                    lon = None,
                )
                if created:
                    created_count += 1

            except Exception as e:
                self.stderr.write(f"Error processing event {entry.get('eventid')}: {e}")

        self.stdout.write(f"Successfully loaded {created_count} permits.")