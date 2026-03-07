from django.core.management import BaseCommand
import requests
from django.utils.dateparse import parse_datetime
from zoneinfo import ZoneInfo
from permits.models import Permit

# ----------------------------------------------------------------------
# Pipeline Overview
#
# Loads film permit records from the NYC Open Data API into Permit table. 
# https://data.cityofnewyork.us/City-Government/Film-Permits/tg4x-b46p/
#
# Steps:
# NYC Open Data API
#     ↓
# fetch JSON dataset
#     ↓
# parse and normalize fields
#     ↓
# safely parse datetime strings
#     ↓
# attach America/New_York timezone to naive timestamps
#     ↓
# upsert records using event_id as the unique key
#     ↓
# store structured permit data in the Permit model
#
# Notes:
# - the API can return missing or malformed datetime values
# - rows missing required start/end datetimes are skipped
# - Django stores timezone-aware datetimes internally in UTC
# ----------------------------------------------------------------------

# NYC Open Data timestamps are returned without timezone information.
# Add America/New_York timezone so Django can safely convert
# Store internally as UTC (settings.py)
NY_TZ = ZoneInfo("America/New_York")


def safe_parse_datetime(value):
    """
    Parse a datetime string from the NYC Open Data API.
    Return None if the value is missing or not a string.
    """
    if not value or not isinstance(value, str):
        return None
    return parse_datetime(value)


class Command(BaseCommand):
    help = "Load NYC Film Permit records from NYC Open Data into the Permit table"
    def handle(self, *args, **kwargs):

        url = (
            "https://data.cityofnewyork.us/resource/tg4x-b46p.json"
            "?$limit=25000&$order=eventid"
        )  # request up to 25k rows and return them in event_id order

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            self.stderr.write(f"API request failed: {e}")
            return

        api_count = len(data)
        processed_count = 0
        created_count = 0
        updated_count = 0
        error_count = 0

        for entry in data:
            try:
                event_id = entry.get("eventid")
                event_type = entry.get("eventtype")

                start_datetime = safe_parse_datetime(entry.get("startdatetime"))
                end_datetime = safe_parse_datetime(entry.get("enddatetime"))

                # Skip rows missing required datetime fields
                if not start_datetime or not end_datetime:
                    error_count += 1
                    self.stderr.write(
                        f"Skipping event {event_id}: missing start or end datetime"
                    )
                    continue

                # Attach New York timezone to naive datetimes
                if start_datetime and start_datetime.tzinfo is None:
                    start_datetime = start_datetime.replace(tzinfo=NY_TZ)

                if end_datetime and end_datetime.tzinfo is None:
                    end_datetime = end_datetime.replace(tzinfo=NY_TZ)

                parking_held = entry.get("parkingheld", "")
                borough = entry.get("borough", "")
                community_boards = entry.get("communityboard_s", "")
                category = entry.get("category", "")
                subcategory = entry.get("subcategoryname", "")
                zip_codes = entry.get("zipcode_s", "")

                obj, created = Permit.objects.update_or_create(
                    event_id=event_id,
                    defaults={
                        "event_type": event_type,
                        "start_datetime": start_datetime,
                        "end_datetime": end_datetime,
                        "parking_held": parking_held,
                        "borough": borough,
                        "community_boards": community_boards,
                        "category": category,
                        "subcategory": subcategory,
                        "zip_codes": zip_codes,
                    },
                )

                processed_count += 1

                if created:
                    created_count += 1
                else:
                    updated_count += 1

            except Exception as e:
                error_count += 1
                self.stderr.write(f"Error processing event {entry.get('eventid')}: {e}")

        self.stdout.write(f"API returned {api_count} records.")
        self.stdout.write(f"Processed {processed_count} records.")
        self.stdout.write(f"Created {created_count} new permits.")
        self.stdout.write(f"Updated {updated_count} existing permits.")
        self.stdout.write(f"Encountered {error_count} errors.")
