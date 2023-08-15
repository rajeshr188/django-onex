from math import floor

import django_tables2 as tables
from django.utils.html import format_html
from django_tables2.utils import A

from .models import Loan, Release


class CheckBoxColumnWithName(tables.CheckBoxColumn):
    @property
    def header(self):
        return self.verbose_name


class LoanTable(tables.Table):
    loanid = tables.Column(verbose_name="Loan")

    # https://stackoverflow.com/questions/12939548/select-all-rows-in-django-tables2/12944647#12944647
    selection = tables.CheckBoxColumn(
        accessor="pk", attrs={"th__input": {"onclick": "toggle(this)"}}, orderable=False
    )
    notified = tables.Column(accessor="last_notified")
    months_since_created = tables.Column(verbose_name="Months")

    def render_notified(self, value, record):
        return record.created

    def render_customer(self, record):
        return format_html(
            """<a href="" hx-get="/contact/customer/detail/{}" hx-push-url="true"
                        hx-target="#content" hx-swap="innerHTML transition:true">
            {}</a>""",
            record.customer.pk,
            record.customer.name,
        )

    def value_customer(self, record):
        return record.customer

    def render_loanid(self, record):
        return format_html(
            """
            <a href ="" hx-get="/girvi/girvi/loan/detail/{}/"
                        hx-target="#content" hx-swap="innerHTML transition:true"
                        hx-vals='{{"use_block":"content"}}'
                        hx-push-url="true">{}</a>
            """,
            record.id,
            record.loanid,
        )

    def value_loanid(self, record):
        return record.loanid

    def render_created(self, value):
        return value.date

    def value_created(self, record):
        return record.created.date()

    is_overdue = tables.Column(verbose_name="Overdue?")

    total_interest = tables.Column(
        verbose_name="Interest",
        # footer=lambda table: sum(x.total_interest for x in table.data)
    )
    total_due = tables.Column(
        verbose_name="Due",
        # footer=lambda table: sum(x.total_interest_due for x in table.data)
    )
    loanamount = tables.Column(
        verbose_name="Amount",
        # footer=lambda table: sum(x.loanamount for x in table.data)
    )
    current_value = tables.Column(
        verbose_name="Value",
        # footer = lambda table:sum(x.current_value for x in table.data)
    )
    itemweight = tables.Column(
        verbose_name="Wt",
        # footer = lambda table:sum(x.itemweight for x in table.data)
    )

    class Meta:
        model = Loan
        fields = (
            "selection",
            "id",
            "loanid",
            "created",
            "customer",
            "itemdesc",
            "itemweight",
            "loanamount",
            "total_interest",
            "total_due",
            "current_value",
            "months_since_created",
            "is_overdue",
        )
        # https://stackoverflow.com/questions/37513463/how-to-change-color-of-django-tables-row
        row_attrs = {
            "class": lambda record: "table-success"
            if record.is_released
            else ("table-danger" if record.is_overdue else "table-secondary")
        }
        attrs = {"class": "table table-striped table-hover"}
        empty_text = "There are no loans matching the search criteria..."
        template_name = "table_htmx.html"


class ReleaseTable(tables.Table):
    releaseid = tables.Column(linkify=True)

    class Meta:
        model = Release
        fields = ("id", "releaseid", "created", "loan", "interestpaid")
        attrs = {"class": "table table-sm table-striped table-hover"}
        empty_text = "There are no release matching the search criteria..."
        template_name = "django_tables2/bootstrap5.html"
