from django.shortcuts import render
from contact.models import Customer
# Create your views here.
def home(request):
    customer = Customer.objects.get(id=3256)
    ledger = customer.get_all_cars()
    data = {}
    data['ledger'] = ledger
    # data['cashbal'] = customer.get_cash_balance()
    data['metalbal'] = customer.get_metal_balance()
    return render(request,'ledger/home.html',context = {"data":data,})
