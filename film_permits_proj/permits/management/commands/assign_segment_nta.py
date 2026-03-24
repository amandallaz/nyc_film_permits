"""
Assign NYC Neighborhood Tabulation Area (NTA) to each StreetSegment.

Method: centroid of the segment line falls inside an NTA polygon (EPSG:4326).
Segments whose centroid lies outside all NTAs (water, edge cases) get
nta_match_status=no_match and empty nta fields — rows are not deleted.

NTA GeoJSON: download 2020 NTAs from NYC Open Data / Planning; see nta_data/README.md.
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd
from django.conf import settings
from django.core.management import BaseCommand
from shapely.errors import GEOSException
from shapely.geometry import shape

from permits.models import StreetSegment


def _resolve_nta_columns(gdf_nta):
    """Map common NYC NTA field names (case-insensitive)."""
    lc = {c.lower(): c for c in gdf_nta.columns if c != "geometry"}
    code_col = None
    for key in ("nta2020", "nta2010", "geoid", "ntacode", "nta_code"):
        if key in lc:
            code_col = lc[key]
            break
    name_col = None
    for key in ("ntaname2020", "ntaname2010", "ntaname", "label"):
        if key in lc:
            name_col = lc[key]
            break
    return code_col, name_col


class Command(BaseCommand):
    help = "Assign NYC NTA (neighborhood) to StreetSegment rows using centroid-in-polygon join"

    def add_arguments(self, parser):
        parser.add_argument(
            "--nta-path",
            type=str,
            default="nta_data/nynta2020.geojson",
            help="Path to NTA boundaries GeoJSON (relative to project dir with manage.py)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Rows per bulk_update batch",
        )

    def handle(self, *args, **options):
        base_dir = Path(settings.BASE_DIR)
        nta_path = Path(options["nta_path"])
        if not nta_path.is_absolute():
            nta_path = base_dir / nta_path

        if not nta_path.exists():
            self.stderr.write(
                f"NTA file not found: {nta_path}\n"
                "Download 2020 NTAs as GeoJSON and save as nta_data/nynta2020.geojson "
                "(see film_permits_proj/nta_data/README.md)."
            )
            return

        self.stdout.write(f"Loading NTAs from {nta_path}...")
        gdf_nta = gpd.read_file(nta_path)
        if gdf_nta.crs is None:
            gdf_nta.set_crs(4326, inplace=True)
        else:
            gdf_nta = gdf_nta.to_crs(epsg=4326)

        code_col, name_col = _resolve_nta_columns(gdf_nta)
        if not code_col and not name_col:
            self.stderr.write(
                "Could not find NTA code/name columns in GeoJSON. "
                f"Columns present: {list(gdf_nta.columns)}"
            )
            return
        self.stdout.write(
            f"Using NTA columns: code={code_col!r}, name={name_col!r}"
        )

        rows = []
        for seg in StreetSegment.objects.all().iterator(chunk_size=2000):
            try:
                geom = shape(seg.geometry_geojson)
                centroid = geom.centroid
            except (GEOSException, TypeError, KeyError, ValueError) as e:
                rows.append(
                    {
                        "segment_id": seg.segment_id,
                        "geometry": None,
                        "error": str(e),
                    }
                )
                continue
            rows.append(
                {
                    "segment_id": seg.segment_id,
                    "geometry": centroid,
                    "error": None,
                }
            )

        gdf_pts = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
        valid = gdf_pts[gdf_pts.geometry.notna()].copy()
        invalid_ids = set(gdf_pts.loc[gdf_pts.geometry.isna(), "segment_id"])

        joined = valid.sjoin(gdf_nta, how="left", predicate="within")
        joined = joined.drop_duplicates(subset=["segment_id"], keep="first")

        nta_by_id = {}
        for _, row in joined.iterrows():
            sid = row["segment_id"]
            idx_right = row.get("index_right")
            if pd.isna(idx_right):
                nta_by_id[sid] = ("", "", "no_match")
                continue
            code = ""
            name = ""
            if code_col is not None and code_col in row.index:
                v = row[code_col]
                if v is not None and not pd.isna(v):
                    code = str(v).strip()
            if name_col is not None and name_col in row.index:
                v = row[name_col]
                if v is not None and not pd.isna(v):
                    name = str(v).strip()
            if not code and not name:
                nta_by_id[sid] = ("", "", "no_match")
            else:
                nta_by_id[sid] = (code, name, "matched")

        batch_size = options["batch_size"]
        to_update = []
        total = 0
        no_match = 0
        matched = 0
        bad_geom = 0

        for seg in StreetSegment.objects.all().iterator(chunk_size=2000):
            if seg.segment_id in invalid_ids:
                seg.nta_code = ""
                seg.nta_name = ""
                seg.nta_match_status = "bad_geometry"
                bad_geom += 1
            elif seg.segment_id in nta_by_id:
                code, name, status = nta_by_id[seg.segment_id]
                seg.nta_code = code[:20] if code else ""
                seg.nta_name = name[:255] if name else ""
                seg.nta_match_status = status
                if status == "no_match":
                    no_match += 1
                else:
                    matched += 1
            else:
                seg.nta_code = ""
                seg.nta_name = ""
                seg.nta_match_status = "no_match"
                no_match += 1

            to_update.append(seg)
            total += 1
            if len(to_update) >= batch_size:
                StreetSegment.objects.bulk_update(
                    to_update,
                    ["nta_code", "nta_name", "nta_match_status"],
                )
                to_update = []

        if to_update:
            StreetSegment.objects.bulk_update(
                to_update,
                ["nta_code", "nta_name", "nta_match_status"],
            )

        self.stdout.write(
            f"Finished. Labeled {total} segments: matched={matched}, "
            f"no_match={no_match}, bad_geometry={bad_geom}."
        )
