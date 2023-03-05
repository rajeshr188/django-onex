import django_tables2 as tables
from django.utils.html import format_html
from django_tables2.utils import A

from .models import Customer


class ImageColumn(tables.Column):
    def render(self, value):
        return format_html(
            '<img src="{}" width="50" height="50" class="img-fluid img-thumbnail" alt={}/>',
            value.url,
            value.name,
        )


class CustomerTable(tables.Table):
    name = tables.Column(linkify=True)
    pic = ImageColumn()

    addloan = tables.LinkColumn(
        "girvi_loan_create",
        args=[A("pk")],
        attrs={"a": {"class": "btn fa-solid fa-plus", "role": "button"}},
        orderable=False,
        empty_values=(),
    )
    edit = tables.LinkColumn(
        "contact_customer_update",
        args=[A("pk")],
        attrs={"a": {"class": "btn fa-solid fa-pen-to-square", "role": "button"}},
        orderable=False,
        empty_values=(),
    )
    # remove = tables.LinkColumn(
    #     "contact_customer_delete",
    #     args=[A("pk")],
    #     attrs={"a": {"class": "btn fa-solid fa-trash", "role": "button"}},
    #     orderable=False,
    #     empty_values=(),
    # )
    remove = tables.Column(orderable=False, empty_values=())

    # add a method to get name relatedas related to address phonenumber in one column
    def render_name(self, record):
        return f"{record.name} {record.relatedas} {record.relatedto}"

    def render_Address(self, record):
        if record.contactno.exists():
            numbers = [no.number for no in record.contactno.all()]
            return f"{record.Address} {numbers}"
        else:
            return f"{record.Address}"

    def render_addloan(self):
        return ""

    def render_edit(self):
        return ""

    # def render_remove(self):
    #     return ""
    def render_remove(self, record):
        return format_html(
            '<a hx-delete="/contact/customer/{}/delete/"  class="btn fa-solid fa-trash" role="button"></a>',
            record.pk,
        )

    class Meta:
        model = Customer
        fields = ("id", "pic", "name", "Address")
        attrs = {
            "class": "table table-sm text-center table-hover table-striped",
        }
        empty_text = "There are no customers matching the search criteria..."
        # template_name='django_tables2/bootstrap5.html'
        template_name = "table_htmx.html"
