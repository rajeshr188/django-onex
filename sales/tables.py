import django_tables2 as tables
from django_tables2.utils import A
from .models import Invoice,Receipt
from django.utils.html import format_html

class InvoiceTable(tables.Table):
    id = tables.LinkColumn('sales_invoice_detail',args=[A('id')])
    customer = tables.LinkColumn('contact_customer_detail',text=lambda record: f"{record.customer.name}{record.customer.area}",args=[A('customer.id')])
    paid = tables.Column(accessor='get_total_receipts',verbose_name="Paid",orderable=False)
    edit = tables.LinkColumn('sales_invoice_update', args=[A('id')],attrs={'a':{"class":"btn btn-outline-info","role":"button"}}, orderable=False, empty_values=())
    delete = tables.LinkColumn('sales_invoice_delete', args=[A('id')],attrs={'a':{"class":"btn btn-outline-danger","role":"button"}}, orderable=False, empty_values=())

    def render_created(self,value):
        return value.date
    def render_due_date(self,value):
        return value.strftime("%d/%m/%Y") if value else value
    def render_edit(self):
        return 'Edit'
    def render_delete(self):
        return 'Delete'

    class Meta:
        model = Invoice
        fields = ('id','created','customer','balancetype','paymenttype',
                    'balance','status','term','due_date')

        attrs = {"class": "table table-sm table-striped table-bordered"}
        empty_text = "No Invoices Found matching your search..."


class ReceiptTable(tables.Table):
    id = tables.LinkColumn('sales_receipt_detail',args=[A('id')])
    customer = tables.LinkColumn('contact_customer_detail',args=[A('customer.id')])
    edit = tables.LinkColumn('sales_receipt_update', args=[A('id')],attrs={'a':{"class":"btn btn-outline-info","role":"button"}}, orderable=False, empty_values=())
    delete = tables.LinkColumn('sales_receipt_delete', args=[A('id')],attrs={'a':{"class":"btn btn-outline-danger","role":"button"}}, orderable=False, empty_values=())

    def render_customer(self,value):
        return f"{value.name}"
    def render_created(self,value):
        return value.date
    def render_edit(self):
        return 'Edit'
    def render_delete(self):
        return 'Delete'

    class Meta:
        model = Receipt
        fields = ('id','created','customer','type','total','description','status')
        attrs = {"class": "table table-striped table-bordered"}
        empty_text = "No Receipts Found matching your search..."
