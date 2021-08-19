import django_tables2 as tables
from django_tables2.utils import A
from .models import Invoice,Payment

class InvoiceTable(tables.Table):
    id = tables.Column(linkify = True)
    supplier = tables.Column(linkify = True)
    # paid = tables.Column(accessor='get_total_payments',verbose_name="Paid",
    #                 orderable=False)
    edit = tables.Column(linkify =('purchase_invoice_update',[tables.A("pk")]),
                empty_values=(),
                attrs={'a': {"class": "btn btn-outline-info", "role": "button"}})
    remove = tables.Column(linkify=('purchase_invoice_delete',[tables.A("pk")]),
                empty_values=(),
                attrs={'a': {"class": "btn btn-outline-danger", "role": "button"}})
   
    def render_supplier(self,value):
        return value.name
    def render_created(self,value):
        return value.date
    def render_edit(self):
        return 'Edit'
    def render_remove(self):
        return 'Delete'

    class Meta:
        model = Invoice
        fields = ('id','created','supplier','balancetype','metaltype',
                    'rate','net_wt','balance','status','is_gst','posted','term','due_date')

        attrs = {"class": "table table-striped table-bordered"}
        empty_text = "No Invoices Found matching your search..."


class PaymentTable(tables.Table):
    id = tables.Column(linkify = True)
    supplier = tables.Column(linkify = True)
    # edit = tables.LinkColumn('purchase_payment_update', 
    #                     args=[A('pk')],attrs={'a':{"class":"btn btn-outline-info","role":"button"}}, 
    #                     orderable=False, empty_values=())
    remove = tables.LinkColumn('purchase_payment_delete',
                         args=[A('pk')],attrs={'a':{"class":"btn btn-outline-danger","role":"button"}},
                         orderable=False, empty_values=())

    def render_supplier(self,value):
        return value.name
    def render_created(self,value):
        return value.date
    # def render_edit(self):
    #     return 'Edit'
    def render_remove(self):
        return 'Delete'

    class Meta:
        model = Payment
        fields = ('id','created','supplier','type','total','status','posted','description')
        attrs = {"class": "table table-striped table-bordered"}
        empty_text = "No Receipts Found matching your search..."
