import django_tables2 as tables
from django_tables2.utils import A
from .models import Customer,Supplier
from django.utils.html import format_html

class ImageColumn(tables.Column):
    def render(self, value):
        return format_html('<img src="{}" width="50" height="50" class="img-fluid img-thumbnail" alt={}/>', value.url,value.name)
class CustomerTable(tables.Table):
    name = tables.LinkColumn('contact_customer_detail', args=[A('slug')])
    pic = ImageColumn()
    relatedas=tables.Column(orderable=False)
    loan=tables.Column(accessor='get_total_loans',verbose_name='No.of Loans')
    loanamount = tables.Column(accessor='get_total_loanamount',verbose_name='Loan Amount')
    gweight=tables.Column(accessor='get_gold_weight',verbose_name='Gold')
    sweight=tables.Column(accessor='get_silver_weight',verbose_name='Silver')
    # interestdue = tables.Column(accessor='get_interestdue',verbose_name='Interest')
    edit = tables.LinkColumn('contact_customer_update', args=[A('slug')],attrs={'a':{"class":"btn btn-outline-info","role":"button"}}, orderable=False, empty_values=())
    delete = tables.LinkColumn('contact_customer_delete', args=[A('slug')],attrs={'a':{"class":"btn btn-outline-danger","role":"button"}}, orderable=False, empty_values=())

    def render_edit(self):
        return 'Edit'
    def render_delete(self):
        return 'Delete'

    class Meta:
        model = Customer
        fields = ('pic','id','name',
                    'loan','loanamount','gweight','sweight',
                    # 'interestdue',
                    'relatedto','relatedas', 'address', 'area','phonenumber')
        attrs = {"class": "table table-striped table-bordered"}
        empty_text = "There are no customers matching the search criteria..."

class SupplierTable(tables.Table):
    name = tables.LinkColumn('contact_supplier_detail', args=[A('slug')])
    pic = ImageColumn()
    edit = tables.LinkColumn('contact_supplier_update', args=[A('slug')],attrs={'a':{"class":"btn btn-outline-info","role":"button"}}, orderable=False, empty_values=())
    delete = tables.LinkColumn('contact_supplier_delete', args=[A('slug')],attrs={'a':{"class":"btn btn-outline-danger","role":"button"}}, orderable=False, empty_values=())

    def render_edit(self):
        return 'Edit'
    def render_delete(self):
        return 'Delete'
    class Meta:
        model = Supplier
        fields = ('pic','id','name','phonenumber','organisation'
                    )
        attrs = {"class": "table table-striped table-bordered"}
        empty_text = "There are no customers matching the search criteria..."
