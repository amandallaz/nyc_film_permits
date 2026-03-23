from django.core.management.base import BaseCommand
from permits.models import PermitBlock
from decouple import config
import requests
import time


SUBSCRIPTION_KEY = config("SUBSCRIPTION_KEY")


class Command(BaseCommand):
    help = "Match unique PermitBlock street blocks to official street segments using Geoclient"

    def handle(self, *args, **options):

        blocks = (
            PermitBlock.objects
            .filter(segment_id__exact="")
            .values(
                "on_street",
                "cross_street_one",
                "cross_street_two",
                "borough",
            )
            .distinct()
        )

        total = blocks.count()
        self.stdout.write(f"Matching {total} unique permit blocks")

        url = "https://api.nyc.gov/geoclient/v2/blockface.json"

        success = 0
        failed = 0
        rows_updated = 0

        for idx, block in enumerate(blocks, start=1):

            on_street = block["on_street"]
            cross1 = block["cross_street_one"]
            cross2 = block["cross_street_two"]
            borough = block["borough"]

            if not on_street or not cross1 or not cross2:
                updated = (
                    PermitBlock.objects.filter(
                        on_street=on_street,
                        cross_street_one=cross1,
                        cross_street_two=cross2,
                        borough=borough,
                        segment_id__exact="",
                    )
                    .update(segment_match_status="missing_streets")
                )
                rows_updated += updated
                failed += 1
                continue

            params = {
                "onStreet": on_street,
                "crossStreetOne": cross1,
                "crossStreetTwo": cross2,
                "borough": borough,
            }

            headers = {
                "Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY
            }

            try:
                response = requests.get(url, params=params, headers=headers, timeout=10)

                if response.status_code != 200:
                    updated = (
                        PermitBlock.objects.filter(
                            on_street=on_street,
                            cross_street_one=cross1,
                            cross_street_two=cross2,
                            borough=borough,
                            segment_id__exact="",
                        )
                        .update(segment_match_status="api_error")
                    )
                    rows_updated += updated
                    failed += 1
                    continue

                data = response.json()["blockface"]
                segment_id = data["segmentIdentifier"]

                updated = (
                    PermitBlock.objects.filter(
                        on_street=on_street,
                        cross_street_one=cross1,
                        cross_street_two=cross2,
                        borough=borough,
                        segment_id__exact="",
                    )
                    .update(
                        segment_id=segment_id,
                        segment_match_status="matched",
                    )
                )

                rows_updated += updated
                success += 1

            except Exception:
                updated = (
                    PermitBlock.objects.filter(
                        on_street=on_street,
                        cross_street_one=cross1,
                        cross_street_two=cross2,
                        borough=borough,
                        segment_id__exact="",
                    )
                    .update(segment_match_status="exception")
                )
                rows_updated += updated
                failed += 1

            if idx % 250 == 0:
                self.stdout.write(
                    f"[{idx}/{total}] matched={success} failed={failed} rows_updated={rows_updated}"
                )

            time.sleep(0.05)

        self.stdout.write(f"Unique blocks processed: {total}")
        self.stdout.write(f"Unique blocks matched: {success}")
        self.stdout.write(f"Unique blocks failed: {failed}")
        self.stdout.write(f"PermitBlock rows updated: {rows_updated}")