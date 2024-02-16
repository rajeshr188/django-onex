from math import floor

import django_tables2 as tables
from django.utils.html import format_html
from django_tables2.utils import A

from .models import Loan, Release


class ImageColumn(tables.Column):
    def render(self, value):
        return format_html(
            '<img src="{}" width="50" height="50" class="img-fluid img-thumbnail" alt={}/>',
            value.url,
            value.name,
        )


class CheckBoxColumnWithName(tables.CheckBoxColumn):
    @property
    def header(self):
        return self.verbose_name


class LoanTable(tables.Table):
    loan_id = tables.Column(verbose_name="ID")
    loan_date = tables.Column(verbose_name="Date")
    # pic = ImageColumn()
    # https://stackoverflow.com/questions/12939548/select-all-rows-in-django-tables2/12944647#12944647
    selection = tables.CheckBoxColumn(
        accessor="pk",
        attrs={"th__input": {"onclick": "toggle(this)"}},
        orderable=False,
        exclude_from_export=True,
    )
    # notified = tables.Column(accessor="last_notified", exclude_from_export=True)
    months_since_created = tables.Column(
        verbose_name="Months", exclude_from_export=True
    )
    total_weight = tables.Column(verbose_name="Weight", empty_values=())

    # def render_notified(self, value, record):
    #     return record.created

    def render_customer(self, record):
        return format_html(
            """<a href="" hx-get="/contact/customer/detail/{}" hx-push-url="true"
                        hx-target="#content" hx-swap="innerHTML transition:true">
            {}</a>""",
            record.customer.pk,
            record.customer.name,
        )

    def value_customer(self, record):
        return record.customer.name

    def render_total_weight(self, record):
        result = []
        for item in record.get_weight:
            item_type = item["itemtype"]
            total_weight_purity = round(item["total_weight"])
            result.append(f"{item_type}:{total_weight_purity}")

        # Join the results into a single string
        pure = " gms,".join(result)
        return f"{pure} gms"

    def value_total_weight(self, record):
        result = []
        for item in record.get_weight:
            item_type = item["itemtype"]
            total_weight_purity = round(item["total_weight"])
            result.append(f"{item_type}:{total_weight_purity}")

        # Join the results into a single string
        pure = " gms,".join(result)
        return f"{pure} gms"

    def render_loan_id(self, record):
        return format_html(
            """
            <a href ="" hx-get="/girvi/girvi/loan/detail/{}/"
                        hx-target="#content" hx-swap="innerHTML transition:true"
                        hx-vals='{{"use_block":"content"}}'
                        hx-push-url="true">{}</a>
            """,
            record.id,
            record.loan_id,
        )

    def value_loan_id(self, record):
        return record.loan_id

    def render_loan_date(self, value):
        return value.date

    def value_loan_date(self, record):
        return record.loan_date.date()

    # is_overdue = tables.Column(verbose_name="Overdue?")
    # total_loan_amount = tables.Column(
    #     verbose_name="Amount",
    #     footer = lambda table: sum(x.loan_amount for x in table.data)
    # )
    # total_interest = tables.Column(
    #     verbose_name="Interest",
    #     # footer=lambda table: sum(x.total_interest for x in table.data)
    # )
    total_due = tables.Column(verbose_name="Due")
    def value_total_due(self, record):
        return record.total_due
    current_value = tables.Column(verbose_name="Value")
    def value_current_value(self, record):
        return record.current_value

    class Meta:
        model = Loan
        fields = (
            "selection",
            # "id",
            "loan_id",
            "loan_date",
            "customer",
            # "pic",
            "item_desc",
            "total_weight",
            "loan_amount",
            "total_interest",
            "total_due",
            "current_value",
            "months_since_created",
            # "is_overdue",
        )
        # https://stackoverflow.com/questions/37513463/how-to-change-color-of-django-tables-row
        row_attrs = {
            "class": lambda record: "table-success"
            if record.is_released
            else ("table-danger" if record.is_overdue else "table-secondary")
        }
        attrs = {
            "class": "table table-sm table-bordered table-striped-columns table-hover"
        }
        empty_text = "There are no loans matching the search criteria..."
        template_name = "table_htmx.html"


class ReleaseTable(tables.Table):
    release_id = tables.Column(linkify=True)
    loan = tables.Column(linkify=True)

    def render_loan(self, record):
        return format_html(
            """
            <a href ="" hx-get="/girvi/girvi/loan/detail/{}/"
                        hx-target="#content" hx-swap="innerHTML transition:true"
                        hx-vals='{{"use_block":"content"}}'
                        hx-push-url="true">{}</a>
            """,
            record.loan.id,
            record.loan.loan_id,
        )

    def render_release_id(self, record):
        return format_html(
            """
            <a href ="" hx-get="/girvi/girvi/release/detail/{}/"
                        hx-target="#content" hx-swap="innerHTML transition:true"
                        
                        hx-push-url="true">{}</a>
            """,
            record.id,
            record.release_id,
        )

    class Meta:
        model = Release
        fields = ("id", "release_id", "release_date")
        attrs = {"class": "table table-sm table-striped-columns table-hover"}
        empty_text = "There are no release matching the search criteria..."
        # template_name = "django_tables2/bootstrap5.html"
        template_name = "table_htmx.html"
