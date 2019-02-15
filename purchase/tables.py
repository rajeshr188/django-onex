import django_tables2 as tables
from django_tables2.utils import A
from .models import Invoice,Payment
from django.utils.html import format_html

class InvoiceTable(tables.Table):
    id = tables.LinkColumn('purchase_invoice_detail',args=[A('pk')])
    supplier = tables.LinkColumn('contact_supplier_detail',args=[A('supplier.id')])
    paid = tables.Column(accessor='get_total_payments',verbose_name="Paid",orderable=False)
    edit = tables.LinkColumn('purchase_invoice_update', args=[A('pk')],attrs={'a':{"class":"btn btn-outline-info","role":"button"}}, orderable=False, empty_values=())
    delete = tables.LinkColumn('purchase_invoice_delete', args=[A('pk')],attrs={'a':{"class":"btn btn-outline-danger","role":"button"}}, orderable=False, empty_values=())

    def render_supplier(self,value):
        return value.name
    def render_created(self,value):
        return value.date
    def render_edit(self):
        return 'Edit'
    def render_delete(self):
        return 'Delete'

    class Meta:
        model = Invoice
        fields = ('id','created','supplier','balancetype','paymenttype',
                    'rate','balance','status')

        attrs = {"class": "table table-striped table-bordered"}
        empty_text = "No Invoices Found matching your search..."


class PaymentTable(tables.Table):
    id = tables.LinkColumn('purchase_payment_detail',args=[A('pk')])
    supplier = tables.LinkColumn('contact_supplier_detail',args=[A('supplier.id')])
    edit = tables.LinkColumn('purchase_payment_update', args=[A('pk')],attrs={'a':{"class":"btn btn-outline-info","role":"button"}}, orderable=False, empty_values=())
    delete = tables.LinkColumn('purchase_payment_delete', args=[A('pk')],attrs={'a':{"class":"btn btn-outline-danger","role":"button"}}, orderable=False, empty_values=())

    def render_supplier(self,value):
        return value.name
    def render_created(self,value):
        return value.date
    def render_edit(self):
        return 'Edit'
    def render_delete(self):
        return 'Delete'

    class Meta:
        model = Payment
        fields = ('id','created','supplier','type','total','description')
        attrs = {"class": "table table-striped table-bordered"}
        empty_text = "No Receipts Found matching your search..."
