from django.core.management import BaseCommand
from permits.models import Permit, PermitBlock

# ----------------------------------------------------------------------
# Pipeline Overview (V2 Build PermitBlocks)
#
# Converts Permit.parking_held strings into normalized and parsed
# PermitBlock rows.
#
# Example:
# "BROADWAY between WARREN STREET and MURRAY STREET,
#  BROADWAY between CHAMBERS STREET and READE STREET"
#
# becomes:
# 1 | BROADWAY between WARREN STREET and MURRAY STREET
# 2 | BROADWAY between CHAMBERS STREET and READE STREET
#
# Steps:
# Permit.parking_held
#     ↓
# split comma-separated blocks
#     ↓
# normalize whitespace
#     ↓
# parse blockface ("ON_STREET between CROSS1 and CROSS2")
#     ↓
# create PermitBlock rows with parsed street components
# ----------------------------------------------------------------------


# Normalize inconsistent spacing in street strings.
# Example: "WEST   58 STREET between 10 AVENUE and 11 AVENUE"
# becomes:  "WEST 58 STREET between 10 AVENUE and 11 AVENUE"
def normalize_whitespace(text):
    return " ".join(text.split())

# Parse a blockface string into its street components.
# Example: "BROADWAY between WARREN STREET and MURRAY STREET"
# becomes: ("BROADWAY", "WARREN STREET", "MURRAY STREET")
def parse_blockface(text):
    try:
        parts = text.split(" between ")
        on_street = parts[0].strip()
        cross1, cross2 = parts[1].split(" and ")
        return on_street, cross1.strip(), cross2.strip()
    except Exception:
        return None, None, None
    
class Command(BaseCommand):
    help = "Build PermitBlock rows by splitting and parsing Permit.parking_held"

    def handle(self, *args, **options):

        # idempotent: reset blocks so the command can be rerun cleanly
        PermitBlock.objects.all().delete()

        created = 0
        parse_failures = 0
        permit_count = 0

        for permit in Permit.objects.all():
            permit_count += 1

            segments = permit.parking_held.split(",")

            for order, segment in enumerate(segments, start=1):

                raw = normalize_whitespace(segment.strip())

                if not raw:  # skip empty segments created by splitting
                    continue

                on_street, cross1, cross2 = parse_blockface(raw)

                if not all([on_street, cross1, cross2]):
                    parse_failures += 1

                PermitBlock.objects.create(
                    permit=permit,
                    block_order=order,
                    raw_location=raw,
                    borough=permit.borough,
                    on_street=on_street or "",
                    cross_street_one=cross1 or "",
                    cross_street_two=cross2 or "",
                )

                created += 1

        self.stdout.write(f"Permits processed: {permit_count}")
        self.stdout.write(f"Created {created} PermitBlock rows")
        self.stdout.write(f"Parse failures: {parse_failures}")
