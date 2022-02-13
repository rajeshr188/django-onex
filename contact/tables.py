import django_tables2 as tables
from django_tables2.utils import A
from .models import Customer
from django.utils.html import format_html

class ImageColumn(tables.Column):
    def render(self, value):
        return format_html('<img src="{}" width="50" height="50" class="img-fluid img-thumbnail" alt={}/>', value.url,value.name)

class CustomerTable(tables.Table):
    name = tables.LinkColumn('contact_customer_detail', args=[A('pk')])
    pic = ImageColumn()
    # relatedas=tables.Column(orderable=False)
    loan=tables.Column(accessor='get_loans_count',verbose_name='Loans',orderable=False)

    addloan = tables.LinkColumn('girvi_loan_create',args=[A('pk')],attrs={'a':{"class":"btn btn-outline-info","role":"button"}}, orderable=False, empty_values=())
    # edit = tables.LinkColumn('contact_customer_update', args=[A('pk')],attrs={'a':{"class":"btn btn-outline-info","role":"button"}}, orderable=False, empty_values=())
    # remove = tables.LinkColumn('contact_customer_delete', args=[A('pk')],attrs={'a':{"class":"btn btn-outline-danger","role":"button"}}, orderable=False, empty_values=())
    remove = tables.Column(orderable=False, empty_values=())
 
    # add a method to get name relatedas related to address phonenumber in one column
    def render_name(self,record):
        return f"{record.name} {record.relatedas} {record.relatedto}"
    def render_Address(self,record):
        return f"{record.Address} {record.phonenumber}"
    def render_addloan(self):
        return '+ Loan'
    # def render_edit(self):
    #     return 'Edit'
    # def render_remove(self):
    #     return 'Delete'
    def render_remove(self,record):
        return format_html('<a hx-post="/contact/customer/{}/delete/"  class="btn btn-outline-danger" role="button">Delete</a>', record.pk)

    class Meta:
        model = Customer
        fields = (
                    'id','pic','name','Address')
        attrs = {
            "class": "table table-sm text-center  table-striped table-bordered",
            
            }
        empty_text = "There are no customers matching the search criteria..."
        template_name='django_tables2/bootstrap4.html'

