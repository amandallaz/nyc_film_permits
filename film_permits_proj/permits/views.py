from django.shortcuts import render
from .models import Permit

def permit_list_view(request):
    permits = Permit.objects.all().order_by('start_datetime') #[:100]  #recent 100
    return render(request, 'permits/permit_list.html', {'permits': permits})

# leaflet
# def permit_map_view(request):
#     permits = Permit.objects.exclude(lat__isnull=True, lon__isnull=True)
#     return render(request, "permits/permit_map.html", {"permits": permits})

def permit_map_view(request):
    permits_qs = Permit.objects.exclude(lat__isnull=True, lon__isnull=True)
    permits = list(permits_qs.values(
                                'event_id', 
                                'event_type', 
                                'borough',
                                'start_datetime', 
                                'end_datetime', 
                                'lat', 
                                'lon'))
    return render(request, "permits/permit_map.html", {"permits": permits})