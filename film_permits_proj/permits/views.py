from django.shortcuts import render
from .models import Permit

def permit_list_view(request):
    permits = Permit.objects.all().order_by('start_datetime') #[:100]  #recent 100
    return render(request, 'permits/permit_list.html', {'permits': permits})



