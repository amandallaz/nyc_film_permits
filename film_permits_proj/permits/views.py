from django.shortcuts import render
from .models import Permit


def permit_list_view(request):
    permits = Permit.objects.order_by("start_datetime")
    return render(request, "permits/permit_list.html", {"permits": permits})


def permit_map_view(request):
    """
    Returns permits with geocoded coordinates for map display.

    Current implementation uses the first permit location midpoint (V1).
    Future versions will use PermitBlock coordinates for more mapping options.
    """

    permits_qs = Permit.objects.exclude(lat__isnull=True).exclude(lon__isnull=True)

    permits = list(
        permits_qs.values(
            "event_id",
            "event_type",
            "borough",
            "start_datetime",
            "end_datetime",
            "lat",
            "lon",
        )
    )

    return render(request, "permits/permit_map.html", {"permits": permits})