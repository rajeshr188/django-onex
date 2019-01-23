from controlcenter import Dashboard,widgets
from sales.models import Invoice,Receipt,Month
from django.db.models import  Sum,Count
from contact.models import Customer

class InvList(widgets.ItemList):
    model=Invoice
    list_display = ('pk','customer','balance')

class Invoice_count(widgets.SingleBarChart):
    # label and series
    values_list = ('month', 'count_items')
    # Data source
    # queryset = Invoice.objects.extra(select={'date': 'DATE(created)'},order_by=['date']).values('date').annotate(count_items=Count('id'))
    queryset=Invoice.objects.annotate(month = Month('created')).values('month').order_by('month').annotate(count_items=Count('id'))
    # limit_to = 10

class Invoice_cash_value(widgets.SingleBarChart):
    # label and series
    values_list = ('month', 'total')
    # Data source
    # queryset = Invoice.objects.extra(select={'date': 'DATE(created)'},order_by=['date']).values('date').annotate(count_items=Count('id'))
    queryset=Invoice.objects.filter(balancetype="Cash").annotate(month = Month('created')).values('month').order_by('month').annotate(total=Sum('balance'))
    # limit_to = 10
    def legend(self):
        # Displays labels in legend
        return [x for x, y in self.values]


class Invoice_metal_value(widgets.SingleBarChart):
    # label and series
    values_list = ('month', 'total')
    # Data source
    # queryset = Invoice.objects.extra(select={'date': 'DATE(created)'},order_by=['date']).values('date').annotate(count_items=Count('id'))
    queryset=Invoice.objects.filter(balancetype="Metal").annotate(month = Month('created')).values('month').order_by('month').annotate(total=Sum('balance'))
    # limit_to = 10


class MyDash(Dashboard):
    widgets = (InvList,Invoice_count,Invoice_cash_value,Invoice_metal_value)
