from collections import defaultdict
from pathlib import Path

import geopandas as gpd
from django.conf import settings
from django.shortcuts import render
from shapely.geometry import mapping

from permits.management.commands.assign_segment_nta import _resolve_nta_columns

from .models import Permit, PermitBlock, StreetSegment


# Hero map: outline + pins for these story NTAs only (exact 2020 names, normalized).
_OUTLINE_NTA_KEYS = frozenset(
    {
        "greenpoint",
        "midtown-times square",
    }
)


def _nta_overlay_for_segments(segments_list, label_top_n=15):
    """
    NTA polygons for map outlines (story NTAs only) + label points.

    Boundaries: Greenpoint, Midtown-Times Square — if they appear in segments_list.
    Street tooltips still carry any segment's nta_name.

    Labels: top `label_top_n` by weight, plus anchors for each story NTA missing
    from that list. Client shows pins only for outline NTAs (short names).
    """

    def _norm_nta(s: str) -> str:
        return (
            (s or "")
            .lower()
            .replace("\u2013", "-")
            .replace("\u2014", "-")
            .replace("\u2019", "'")
        )

    def _show_nta_outline(name: str) -> bool:
        return _norm_nta(name.strip()) in _OUTLINE_NTA_KEYS

    empty = {
        "nta_boundaries": {"type": "FeatureCollection", "features": []},
        "nta_labels": [],
    }
    weights = defaultdict(int)
    for s in segments_list:
        name = (s.get("nta_name") or "").strip()
        if name:
            weights[name] += int(s.get("permit_count") or 0)
    if not weights:
        return empty

    nta_path = Path(settings.BASE_DIR) / "nta_data" / "nynta2020.geojson"
    if not nta_path.exists():
        return empty

    gdf = gpd.read_file(nta_path)
    if gdf.crs is None:
        gdf.set_crs(4326, inplace=True)
    else:
        gdf = gdf.to_crs(4326)

    code_col, name_col = _resolve_nta_columns(gdf)
    if not name_col:
        return empty

    names_set = set(weights.keys())
    gdf = gdf.copy()
    gdf["_nta_match"] = gdf[name_col].astype(str).str.strip()
    sub = gdf[gdf["_nta_match"].isin(names_set)]

    features = []
    label_rows = []
    for _, row in sub.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        nm = str(row[name_col]).strip()
        if _show_nta_outline(nm):
            feat = {
                "type": "Feature",
                "geometry": mapping(geom),
                "properties": {
                    "nta_name": nm,
                },
            }
            if code_col and code_col in row.index:
                feat["properties"]["nta2020"] = str(row[code_col])
            features.append(feat)
        c = geom.centroid
        label_rows.append((nm, float(c.x), float(c.y)))

    top_names = set(
        sorted(weights.keys(), key=lambda n: weights[n], reverse=True)[:label_top_n]
    )
    labels = []
    seen_label = set()
    for nm, lon, lat in label_rows:
        if nm not in top_names or nm in seen_label:
            continue
        seen_label.add(nm)
        labels.append({"text": nm, "coordinates": [lon, lat]})

    # Anchor each story NTA if it is in this view but missing from the top-N label list.
    for key in _OUTLINE_NTA_KEYS:
        if any(_norm_nta(entry["text"]) == key for entry in labels):
            continue
        for nm, lon, lat in label_rows:
            if _norm_nta(nm) == key:
                labels.append({"text": nm, "coordinates": [lon, lat]})
                break

    return {
        "nta_boundaries": {"type": "FeatureCollection", "features": features},
        "nta_labels": labels,
    }


def permit_list_view(request):
    permits = Permit.objects.order_by("start_datetime")
    return render(request, "permits/permit_list.html", {"permits": permits})

def permit_map_view(request):
    """
    Returns geocoded street blocks for map display.

    Uses PermitBlock coordinates instead of permit midpoints.
    """

    blocks_qs = (
        PermitBlock.objects
        .exclude(lat__isnull=True)
        .exclude(lon__isnull=True)
    )

    blocks = list(
        blocks_qs.values(
            "raw_location",
            "borough",
            "lat",
            "lon",
        )
    )

    return render(request, "permits/permit_map.html", {"permits": blocks})

def permit_map_deck_view(request):
    blocks_qs = (
        PermitBlock.objects
        .exclude(lat__isnull=True)
        .exclude(lon__isnull=True)
        .values("lat", "lon", "borough")
    )

    blocks = list(blocks_qs)

    return render(request, "permits/permit_map_deck.html", {"blocks": blocks})

def filming_streets_hero(request):
    # Hero: show top 2% of segments by permit_count.
    p98 = 0.98
    base_qs = StreetSegment.objects.filter(permit_count__gt=0)
    counts = sorted(base_qs.values_list("permit_count", flat=True))
    n = len(counts)
    idx98 = int(p98 * (n - 1)) if n else 0
    cutoff_p98 = counts[idx98] if counts else 0
    total_permits = sum(counts)
    total_segments = n
    raw_permit_count = Permit.objects.count()
    segments = (
        base_qs.filter(permit_count__gte=cutoff_p98)
        .order_by("-permit_count")
        .values(
            "segment_id",
            "street",
            "borough",
            "nta_name",
            "permit_count",
            "geometry_geojson",
        )
    )
    segments_list = list(segments)

    # Only segments we can draw (hero map + rank slider max must match client-side count)
    segments_list = [
        s
        for s in segments_list
        if isinstance(s.get("geometry_geojson"), dict) and s["geometry_geojson"].get("type")
    ]

    highlighted_permits = sum(s["permit_count"] for s in segments_list)
    highlighted_permit_share = (
        round((highlighted_permits / total_permits) * 100) if total_permits else 0
    )
    nta_ctx = _nta_overlay_for_segments(segments_list)

    # Map context: every segment with permits (including top 2%), grey underlay; crimson layers draw on top.
    context_street_features = []
    for row in base_qs.values("geometry_geojson"):
        geom = row.get("geometry_geojson")
        if isinstance(geom, dict) and geom.get("type"):
            context_street_features.append(
                {"type": "Feature", "geometry": geom, "properties": {}}
            )
    context_streets_geojson = {
        "type": "FeatureCollection",
        "features": context_street_features,
    }

    return render(request, "permits/filming_streets_hero.html", {
        "segments": segments_list,
        "total_permits": total_permits,
        "raw_permit_count_display": f"{raw_permit_count:,}",
        "total_segment_count_display": f"{total_segments:,}",
        "highlight_cutoff_p98": cutoff_p98,
        "highlighted_permit_share": highlighted_permit_share,
        "highlighted_segment_count": len(segments_list),
        "context_streets_geojson": context_streets_geojson,
        "nta_boundaries": nta_ctx["nta_boundaries"],
        "nta_labels": nta_ctx["nta_labels"],
    })


def filming_streets_explore(request):
    segments = (
        StreetSegment.objects
        .filter(permit_count__gte=20)
        .values(
            "segment_id",
            "street",
            "borough",
            "permit_count",
            "geometry_geojson",
        )
    )

    return render(request, "permits/filming_streets_explore.html", {
        "segments": list(segments)
    })