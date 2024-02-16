import django_tables2 as tables
from django.utils.html import format_html,format_html_join, escape

from django_tables2.utils import A

from .models import Customer


class ImageColumn(tables.Column):
    def render(self, value):
        return format_html(
            '<img src="{}" width="50" height="50" class="img-fluid img-thumbnail" alt={}/>',
            value.url,
            value.name,
        )
class CustomerExportTable(tables.Table):
    class Meta:
        model = Customer
        fields = ("created","id", "name", "relatedas", "relatedto")  

class CustomerTable(tables.Table):
    name = tables.Column(verbose_name="Name")
    # pic = ImageColumn()
    address = tables.Column(verbose_name="Address", orderable=False, empty_values=())
    phonenumber = tables.Column(verbose_name="Phone Number", orderable=False, empty_values=())
    actions = tables.Column(orderable=False, empty_values=())

    # add a method to get name relatedas related to address phonenumber in one column
    def render_name(self, record):
        return format_html(
            """
                <a href="" hx-get="/contact/customer/detail/{}" 
                            hx-swap="innerHTML transition:true"
                            hx-target="#content" hx-push-url="true">
                {}
                </a>
                """,
            record.id,
            f"{record.name} {record.get_relatedas_display()} {record.relatedto}",
        )
    
    def value_name(self, record):
        return f"{record.name} {record.get_relatedas_display()} {record.relatedto}"


    def render_address(self, record):
        addresses = [[escape(address.doorno), escape(address.street), escape(address.area), escape(address.city), escape(address.zipcode)] for address in record.address.all()]
        return format_html_join('<br>', '{} {} {} {} {}', addresses)

    def value_address(self, record):
        addresses = [[escape(address.doorno), escape(address.street), escape(address.area), escape(address.city), escape(address.zipcode)] for address in record.address.all()]
        return format_html_join('<br>', '{} {} {} {} {}', addresses)

    def render_phonenumber(self, record):
        numbers = [str(no.phone_number.national_number) for no in record.contactno.all()]
        return f"{','.join(numbers)}"

    def value_phonenumber(self, record):
        numbers = [str(no.phone_number.national_number) for no in record.contactno.all()]
        return f"{','.join(numbers)}"
        # return f"{numbers}"

    # never define render_delete it will delete all
    def render_actions(self, record):
        return format_html(
            """
            <div class="btn-group">
                <button type="button" class="btn btn-sm btn-secondary dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-three-dots-vertical" viewBox="0 0 16 16">
  <path d="M9.5 13a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0m0-5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0m0-5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0"/>
</svg>
                </button>
                <ul class="dropdown-menu">
                    <li><a class="dropdown-item" hx-target="#content" hx-get="/girvi/girvi/loan/create/{}"
    #                 hx-push-url="true"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-plus-square" viewBox="0 0 16 16">
    #                 <path d="M14 1a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h12zM2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H2z"/>
    #                 <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/>
    #                 </svg> Loan</a></li>
                    <li><a class="dropdown-item" hx-get="/contact/customer/update/{}"
    #                     hx-push-url="true"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-pencil-square" viewBox="0 0 16 16">
    #                 <path d="M15.502 1.94a.5.5 0 0 1 0 .706L14.459 3.69l-2-2L13.502.646a.5.5 0 0 1 .707 0l1.293 1.293zm-1.75 2.456-2-2L4.939 9.21a.5.5 0 0 0-.121.196l-.805 2.414a.25.25 0 0 0 .316.316l2.414-.805a.5.5 0 0 0 .196-.12l6.813-6.814z"/>
    #                 <path fill-rule="evenodd" d="M1 13.5A1.5 1.5 0 0 0 2.5 15h11a1.5 1.5 0 0 0 1.5-1.5v-6a.5.5 0 0 0-1 0v6a.5.5 0 0 1-.5.5h-11a.5.5 0 0 1-.5-.5v-11a.5.5 0 0 1 .5-.5H9a.5.5 0 0 0 0-1H2.5A1.5 1.5 0 0 0 1 2.5v11z"/>
    #                 </svg> Customer</a></li>
                    <li><a class="dropdown-item" hx-delete="/contact/customer/{}/delete/" hx-confirm="Are you sure?" hx-target="closest tr" hx-swap="outerHTML swap:0.5s"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16">
    #                 <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5Zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5Zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6Z"/>
    #                 <path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1ZM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118ZM2.5 3h11V2h-11v1Z"/>
    #                 </svg>Customer</a></li>
                </ul>
            </div>
            """,
            record.pk,
            record.pk,
            record.pk,
        )
    # def render_actions(self, record):
    #     return format_html(
    #         """
    #         <button class="btn btn-sm btn-primary" hx-target="#content" hx-get="/girvi/girvi/loan/create/{}"
    #                 hx-push-url="true">
    #             <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-plus-square" viewBox="0 0 16 16">
    #                 <path d="M14 1a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h12zM2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H2z"/>
    #                 <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/>
    #                 </svg>
    #             </button>
    #         <button class="btn btn-sm btn-secondary" hx-get="/contact/customer/update/{}"
    #                     hx-push-url="true" >
    #            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-pencil-square" viewBox="0 0 16 16">
    #                 <path d="M15.502 1.94a.5.5 0 0 1 0 .706L14.459 3.69l-2-2L13.502.646a.5.5 0 0 1 .707 0l1.293 1.293zm-1.75 2.456-2-2L4.939 9.21a.5.5 0 0 0-.121.196l-.805 2.414a.25.25 0 0 0 .316.316l2.414-.805a.5.5 0 0 0 .196-.12l6.813-6.814z"/>
    #                 <path fill-rule="evenodd" d="M1 13.5A1.5 1.5 0 0 0 2.5 15h11a1.5 1.5 0 0 0 1.5-1.5v-6a.5.5 0 0 0-1 0v6a.5.5 0 0 1-.5.5h-11a.5.5 0 0 1-.5-.5v-11a.5.5 0 0 1 .5-.5H9a.5.5 0 0 0 0-1H2.5A1.5 1.5 0 0 0 1 2.5v11z"/>
    #                 </svg>
    #             </button>
    #         <button class="btn btn-sm  btn-danger" hx-delete="/contact/customer/{}/delete/"  hx-confirm="Are you sure?" hx-target="closest tr" hx-swap="outerHTML swap:0.5s" >
    #             <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16">
    #                 <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5Zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5Zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6Z"/>
    #                 <path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1ZM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118ZM2.5 3h11V2h-11v1Z"/>
    #                 </svg>
    #             </button>""",
    #         record.pk,
    #         record.pk,
    #         record.pk,
    #     )

    class Meta:
        model = Customer
        fields = ("id", "name")
        attrs = {
            "class": "table table-sm table-bordered text-center table-hover table-striped-columns",
        }
        empty_text = "There are no customers matching the search criteria..."
        # template_name='django_tables2/bootstrap5.html'
        template_name = "table_htmx.html"
