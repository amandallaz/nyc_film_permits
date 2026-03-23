from django.core.management import BaseCommand
from permits.models import StreetSegment
import geopandas as gpd
import json

# lion.gdb
# ↓
# read layer="lion"
# ↓
# reproject to 4326 (converts to lat/lon coordinates)
# ↓
# store a simplified StreetSegment table

class Command(BaseCommand):
    help = "Load NYC LION street segments into StreetSegment"

    def handle(self, *args, **options):
        path = "lion_data/lion.gdb"

        self.stdout.write("Reading LION data...")
        gdf = gpd.read_file(path, layer="lion")

        self.stdout.write("Reprojecting to EPSG:4326...")
        gdf = gdf.to_crs(epsg=4326)

        # keep only the fields we need
        gdf = gdf[["SegmentID", "Street", "LBoro", "RBoro", "geometry"]].copy()

        # drop duplicates
        gdf = gdf.dropna(subset=["SegmentID"]).drop_duplicates(subset=["SegmentID"])

        # idempotent for now
        StreetSegment.objects.all().delete()

        created = 0

        for _, row in gdf.iterrows():
            segment_id = str(row["SegmentID"])
            street = row["Street"] or ""

            # temporary first-pass borough choice
            borough = row["LBoro"] or row["RBoro"] or ""

            geometry_geojson = json.loads(gpd.GeoSeries([row["geometry"]]).to_json())["features"][0]["geometry"]

            StreetSegment.objects.create(
                segment_id=segment_id,
                street=street,
                borough=str(borough),
                geometry_geojson=geometry_geojson,
            )

            created += 1

            if created % 10000 == 0:
                self.stdout.write(f"Loaded {created} street segments...")

        self.stdout.write(f"Finished. Loaded {created} street segments.")