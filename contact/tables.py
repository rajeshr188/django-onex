import django_tables2 as tables
from django_tables2.utils import A
from .models import Customer
from django.utils.html import format_html

class ImageColumn(tables.Column):
    def render(self, value):
        return format_html('<img src="{}" width="50" height="50" class="img-fluid img-thumbnail" alt={}/>', value.url,value.name)
class CustomerTable(tables.Table):
    name = tables.LinkColumn('contact_customer_detail', args=[A('pk')])
    # pic = ImageColumn()
    relatedas=tables.Column(orderable=False)
    # loan=tables.Column(accessor='get_loans_count',verbose_name='No.of Loans',orderable=False)
    # loanamount = tables.Column(accessor='get_total_loanamount',verbose_name='Loan Amount',orderable=False)
    # gweight=tables.Column(accessor='get_gold_weight',verbose_name='Gold')
    # sweight=tables.Column(accessor='get_silver_weight',verbose_name='Silver')
    # interestdue = tables.Column(accessor='get_interestdue',verbose_name='Interest')
    addloan = tables.LinkColumn('girvi_loan_create',args=[A('pk')],attrs={'a':{"class":"btn btn-outline-info","role":"button"}}, orderable=False, empty_values=())
    # edit = tables.LinkColumn('contact_customer_update', args=[A('pk')],attrs={'a':{"class":"btn btn-outline-info","role":"button"}}, orderable=False, empty_values=())
    remove = tables.LinkColumn('contact_customer_delete', args=[A('pk')],attrs={'a':{"class":"btn btn-outline-danger","role":"button"}}, orderable=False, empty_values=())


    def render_addloan(self):
        return '+ Loan'
    # def render_edit(self):
    #     return 'Edit'
    def render_remove(self):
        return 'Delete'

    class Meta:
        model = Customer
        fields = (
                    'id','pic','name',
                    'relatedas','relatedto', 'Address', 'phonenumber')
        attrs = {"class": "table table-sm text-center  table-striped table-bordered"}
        empty_text = "There are no customers matching the search criteria..."
        template_name='django_tables2/bootstrap4.html'

