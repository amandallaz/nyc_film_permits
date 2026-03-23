from django.shortcuts import render
from .models import Permit, PermitBlock, StreetSegment


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

    segments = (
        StreetSegment.objects
        .filter(permit_count__gt=0)
        .order_by("-permit_count")[:100]
    ).values(
        "segment_id",
        "street",
        "borough",
        "permit_count",
        "geometry_geojson"
    )

    return render(request, "permits/filming_streets_hero.html", {
        "segments": list(segments)
    })

def filming_streets_explore(request):

    segments = StreetSegment.objects.filter(
        permit_count__gte=20
    ).values(
        "segment_id",
        "street",
        "borough",
        "permit_count",
        "geometry_geojson"
    )

    return render(request, "permits/filming_streets_explore.html", {
        "segments": list(segments)
    })