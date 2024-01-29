from datetime import date, timedelta
from decimal import Decimal

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.db.models import F, Func, Q, Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from moneyed import Money

from approval.models import ReturnItem
from contact.models import Customer
from dea.models import Journal,JournalEntry#, JournalTypes
from dea.models.moneyvalue import MoneyValueField
from dea.utils.currency import Balance
from invoice.models import PaymentTerm
from product.models import StockLot, StockTransaction

# from sympy import content


class Month(Func):
    function = "EXTRACT"
    template = "%(function)s(MONTH from %(expressions)s)"
    output_field = models.IntegerField()


class Year(Func):
    function = "EXTRACT"
    template = "%(function)s(YEAR from %(expressions)s)"
    output_field = models.IntegerField()


class SalesQueryset(models.QuerySet):
    def is_gst(self, value):
        return self.filter(is_gst=value)

    def is_ratecut(self, value):
        return self.filter(is_ratecut=value)

    def today(self):
        return self.filter(created__date=date.today())

    def cur_month(self):
        return self.filter(
            created__month=date.today().month, created__year=date.today().year
        )

    def total_with_ratecut(self):
        return self.aggregate(
            cash=Sum("balance", filter=Q(balancetype="INR")),
            cash_g=Sum("balance", filter=Q(balancetype="INR", metaltype="Gold")),
            cash_s=Sum("balance", filter=Q(balancetype="INR", metaltype="Silver")),
            cash_g_nwt=Sum("net_wt", filter=Q(balancetype="INR", metaltype="Gold")),
            cash_s_nwt=Sum("net_wt", filter=Q(balancetype="INR", metaltype="Silver")),
            gold=Sum("balance", filter=Q(balancetype="USD")),
            silver=Sum("balance", filter=Q(balancetype="AUD")),
        )

    def with_balance(self):
        return self.annotate(
            gold_balance=Sum(
                "saleitem__metal_balance", filter=Q(metal_balance_currency="USD")
            ),
            silver_balance=Sum(
                "saleitem__metal_balance", filter=Q(metal_balance_currency="EUR")
            ),
            cash_balance=Sum("saleitem__cash_balance"),
        ).select_related("saleitem")

    def with_allocated_payment(self):
        return self.annotate(
            gold_amount=Sum(
                "receiptallocation__allocated",
                filter=Q(receiptallocation__allocated_currency="USD"),
            ),
            silver_amount=Sum(
                "receiptallocation__allocated",
                filter=Q(receiptallocation__allocated_currency="EUR"),
            ),
            cash_amount=Sum(
                "receiptallocation__allocated",
                filter=Q(receiptallocation__allocated_currency="INR"),
            ),
        ).select_related("receiptallocation")

    def with_outstanding_balance(self):
        return self.annotate(
            outstanding_gold_balance=F("gold_amount") - F("sale_balance__gold_balance"),
            outstanding_silver_balance=F("silver_amount")
            - F("sale_balance__silver_balance"),
            outstanding_cash_balance=F("cash_amount") - F("sale_balance__cash_balance"),
        )


class Invoice(Journal):
    
    due_date = models.DateField(null=True, blank=True)
    is_ratecut = models.BooleanField(default=False)
    is_gst = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    status_choices = (
        ("Paid", "Paid"),
        ("PartiallyPaid", "PartiallyPaid"),
        ("Unpaid", "Unpaid"),
    )
    status = models.CharField(max_length=15, choices=status_choices, default="Unpaid")

    # Relationship Fields
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="sales",
        verbose_name="Customer",
    )
    term = models.ForeignKey(
        PaymentTerm,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sale_term",
    )
    # change to foreign
    approval = models.ForeignKey(
        "approval.Approval",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sales",
    )
    objects = SalesQueryset.as_manager()

    class Meta:
        ordering = ("-created_at",)
        get_latest_by = "id"

    def __str__(self):
        return f"{self.id}"

    def get_absolute_url(self):
        return reverse("sales:sales_invoice_detail", kwargs={"pk": self.pk})

    def get_hx_url(self):
        return reverse("sales:hx-detail", kwargs={"id": self.id})

    def get_update_url(self):
        return reverse("sales:sales_invoice_update", args=(self.pk,))

    def get_delete_url(self):
        return reverse("sales:sales_invoice_delete", kwargs={"id": self.id})

    def get_invoiceitem_children(self):
        return self.sale_items.all()

    def get_next(self):
        return Invoice.objects.filter(id__gt=self.id).order_by("id").first()

    def get_previous(self):
        return Invoice.objects.filter(id__lt=self.id).order_by("id").last()

    def get_gross_wt(self):
        return self.sale_items.aggregate(t=Sum("weight"))["t"] or 0

    def get_net_wt(self):
        return self.sale_items.aggregate(t=Sum("net_wt"))["t"] or 0

    @property
    def overdue_days(self):
        return (timezone.now().date() - self.date_due).days

    def deactivate(self):
        self.is_active = False
        self.save(update_fields=["self.is_active"])

    def get_gst(self):
        amount = self.sale_items.aggregate(t=Sum("cash_balance"))["t"] or 0
        gst = Money(amount * Decimal(0.03), "INR")
        return gst

    def save(self, *args, **kwargs):
        if not self.due_date:
            self.due_date = self.created + timedelta(days=self.term.due_days)

        return super(Invoice, self).save(*args, **kwargs)

    @classmethod
    def with_outstanding_balance(cls):
        return cls.objects.annotate(
            total_allocated_cash=Coalesce(
                Sum(
                    "receiptallocation__allocated",
                    filter=Q(receiptallocation__allocated_currency="INR"),
                ),
                0,
                output_field=models.DecimalField(),
            ),
            total_allocated_gold=Coalesce(
                Sum(
                    "receiptallocation__allocated",
                    filter=Q(receiptallocation__allocated_currency="USD"),
                ),
                0,
                output_field=models.DecimalField(),
            ),
            total_allocated_silver=Coalesce(
                Sum(
                    "receiptallocation__allocated",
                    filter=Q(receiptallocation__allocated_currency="EUR"),
                ),
                0,
                output_field=models.DecimalField(),
            ),
        ).annotate(
            outstanding_balance_cash=F("sales_balance__cash_balance")
            - F("total_allocated_cash"),
            outstanding_balance_gold=F("sales_balance__gold_balance")
            - F("total_allocated_gold"),
            outstanding_balance_silver=F("sales_balance__silver_balance")
            - F("total_allocated_silver"),
        )

    def get_allocations(self):
        if self.receiptallocation_set.exists():
            paid = self.receiptallocation_set.aggregate(
                cash=Coalesce(
                    Sum("allocated", filter=Q(allocated_currency="INR")),
                    0,
                    output_field=models.DecimalField(),
                ),
                gold=Coalesce(
                    Sum("allocated", filter=Q(allocated_currency="USD")),
                    0,
                    output_field=models.DecimalField(),
                ),
                silver=Coalesce(
                    Sum("allocated", filter=Q(allocated_currency="EUR")),
                    0,
                    output_field=models.DecimalField(),
                ),
            )
            return Balance(
                [
                    Money(paid["cash"], "INR"),
                    Money(paid["gold"], "USD"),
                    Money(paid["silver"], "EUR"),
                ]
            )
        return Balance(0, "INR")

    def get_balance(self):
        return self.balance - self.get_allocations()

    @property
    def balance(self):
        sale_balance = self.sale_balance
        try:
            return Balance(sale_balance.balances)
        except SaleBalance.DoesNotExist:
            return None

    # def delete(self, *args, **kwargs):
    #     if self.approval:
    #         self.approval.is_billed = False
    #     super(Invoice, self).delete(*args, **kwargs)

    def get_transactions(self):
        """
        if self.approval:

            before 16/4/2023 this logic was used to create sale items from approval items
            if any approval, return and bill

            for i in self.approval.items.filter(status="Pending"):
                apr = ReturnItem.objects.create(
                    line=i, quantity=i.quantity, weight=i.weight
                )
                apr.post()
                i.update_status()
            self.approval.is_billed = True
            self.approval.save()
            self.approval.update_status()
        """

        inv = "GST INV" if self.is_gst else "Non-GST INV"
        cogs = "GST COGS" if self.is_gst else "Non-GST COGS"
        tax = self.get_gst()
        # lt = [
        #     {"ledgerno": "Sales", "ledgerno_dr": "Sundry Debtors", "amount": money},
        #     {"ledgerno": inv, "ledgerno_dr": cogs, "amount": money},
        #     {
        #         "ledgerno": "Output Igst",
        #         "ledgerno_dr": "Sundry Debtors",
        #         "amount": tax,
        #     },
        # ]
        # at = [
        #     {
        #         "ledgerno": "Sales",
        #         "xacttypecode": "Cr",
        #         "xacttypecode_ext": "CRSL",
        #         "account": self.customer.account,
        #         "amount": money + tax,
        #     }
        # ]
        lt, at = [], []
        balance = self.sale_balance
        cash_balance = balance.cash_balance
        gold_balance = balance.gold_balance
        silver_balance = balance.silver_balance
        lt.append(
            {
                "ledgerno": "Sales",
                "ledgerno_dr": "Sundry Debtors",
                "amount": cash_balance,
            }
        )
        lt.append({"ledgerno": inv, "ledgerno_dr": cogs, "amount": cash_balance})
        at.append(
            {
                "ledgerno": "Sales",
                "xacttypecode": "Cr",
                "xacttypecode_ext": "CRSL",
                "account": self.customer.account,
                "amount": cash_balance,
            }
        )
        if self.is_gst:
            lt.append(
                {
                    "ledgerno": "Output Igst",
                    "ledgerno_dr": "Sundry Debtors",
                    "amount": tax,
                },
            )
            at.append(
                {
                    "ledgerno": "Sales",
                    "xacttypecode": "Cr",
                    "xacttypecode_ext": "CRSL",
                    "account": self.customer.account,
                    "amount": tax,
                }
            )
        if gold_balance != 0:
            lt.append(
                {
                    "ledgerno": "Sales",
                    "ledgerno_dr": "Sundry Debtors",
                    "amount": gold_balance,
                }
            )
            lt.append({"ledgerno": inv, "ledgerno_dr": cogs, "amount": gold_balance})
            at.append(
                {
                    "ledgerno": "Sales",
                    "xacttypecode": "Cr",
                    "xacttypecode_ext": "CRSL",
                    "account": self.customer.account,
                    "amount": gold_balance,
                }
            )
        if silver_balance != 0:
            lt.append(
                {
                    "ledgerno": "Sales",
                    "ledgerno_dr": "Sundry Debtors",
                    "amount": silver_balance,
                }
            )
            lt.append({"ledgerno": inv, "ledgerno_dr": cogs, "amount": silver_balance})
            at.append(
                {
                    "ledgerno": "Sales",
                    "xacttypecode": "Cr",
                    "xacttypecode_ext": "CRSL",
                    "account": self.customer.account,
                    "amount": silver_balance,
                }
            )
        return lt, at

    def get_items(self):
        return self.sale_items.all()


class InvoiceItem(models.Model):
    # Fields
    is_return = models.BooleanField(default=False, verbose_name="Return")
    huid = models.CharField(max_length=6, null=True, blank=True, unique=True)
    quantity = models.IntegerField()
    weight = models.DecimalField(max_digits=10, decimal_places=3)
    # remove less stone
    less_stone = models.DecimalField(
        max_digits=10, decimal_places=3, default=0, verbose_name="less wt"
    )
    touch = models.DecimalField(max_digits=10, decimal_places=3)
    wastage = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    net_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    rate = models.DecimalField(max_digits=10, decimal_places=3)
    making_charge = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    hallmark_charge = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    metal_balance = MoneyField(
        max_digits=14, decimal_places=3, default_currency="USD", default=0
    )
    cash_balance = MoneyField(
        max_digits=14, decimal_places=3, default_currency="INR", default=0
    )

    # Relationship Fields
    product = models.ForeignKey(
        StockLot, on_delete=models.CASCADE, related_name="sold_items"
    )
    invoice = models.ForeignKey(
        "sales.Invoice", on_delete=models.CASCADE, related_name="sale_items"
    )
    approval_line = models.ForeignKey(
        "approval.ApprovalLine",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sold_items",
    )
    
    class Meta:
        ordering = ("-pk",)

    def __str__(self):
        return "%s" % self.pk

    def get_absolute_url(self):
        return reverse("sales:sales_invoiceitem_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("sales:sales_invoiceitem_update", args=(self.pk,))

    def get_delete_url(self):
        return reverse(
            "sales:sales_invoiceitem_delete",
            kwargs={"id": self.id, "parent_id": self.invoice.id},
        )

    def get_hx_edit_url(self):
        kwargs = {"parent_id": self.invoice.id, "id": self.id}
        return reverse("sales:hx-invoiceitem-detail", kwargs=kwargs)

    def get_nettwt(self):
        return (self.weight * self.touch) / 100

    # @property
    # def get_total(self):
    #     if self.invoice.is_ratecut:
    #         return self.get_nettwt() * self.invoice.rate
    #     else:
    #         return self.get_nettwt()

    def save(self, *args, **kwargs):
        self.net_wt = self.get_nettwt()
        self.rate = self.rate
        self.metal_balance_currency = (
            "USD" if "gold" in self.product.variant.name else "EUR"
        )
        if self.invoice.is_ratecut:
            self.cash_balance = (
                self.net_wt * self.rate + self.making_charge + self.hallmark_charge
            )
            if self.invoice.is_gst:
                self.cash_balance += self.cash_balance * Decimal(0.03)
            self.metal_balance = 0
        else:
            self.cash_balance = self.making_charge + self.hallmark_charge
            self.metal_balance = self.net_wt
            print(self.metal_balance)
        return super(InvoiceItem, self).save(*args, **kwargs)

    def balance(self):
        return Balance([self.metal_balance, self.cash_balance])


    @transaction.atomic()
    def post(self):
        jrnl_entry = self.invoice.get_journal_entry()
        if not self.is_return:
            if self.approval_line:
                # unpost the approval line to return the stocklot from approvalline
                stock_journal_entry = self.approval_line.get_journal_entry()
                self.approval_line.unpost(stock_journal)
                self.approval_line.update_status()
            # post the invoice item to deduct the stock from stocklot
            self.product.transact(self.weight, self.quantity, jrnl_entry, "S")
        else:
            self.product.transact(self.weight, self.quantity, jrnl_entry, "SR")

    @transaction.atomic()
    def unpost(self):
        jrnl_entry = self.invoice.get_journal_entry()
        if self.is_return:
            self.product.transact(self.weight, self.quantity, jrnl_entry, "S")
        else:
            if self.approval_line:
                # post the approval line to deduct the stock from invoiceitem
                stock_journal_entry = self.approval_line.get_journal()
                self.approval_line.post(stock_journal_entry)
                self.approval_line.update_status()
            self.product.transact(self.weight, self.quantity, jrnl_entry, "SR")


class SaleBalance(models.Model):
    """
    SELECT sales_invoice.id AS voucher_id,
        COALESCE(sum(pi.cash_balance), 0.0) AS cash_balance,
        COALESCE(sum(pi.metal_balance) FILTER (WHERE pi.metal_balance_currency::text = 'USD'::text), 0.0) AS gold_balance,
        COALESCE(sum(pi.metal_balance) FILTER (WHERE pi.metal_balance_currency::text = 'EUR'::text), 0.0) AS silver_balance,
        ARRAY[ROW(COALESCE(sum(pi.cash_balance), 0.0)::numeric(14,0), 'INR'::character varying(3))::money_value, ROW(COALESCE(sum(pi.metal_balance) FILTER (WHERE pi.metal_balance_currency::text = 'USD'::text), 0.0)::numeric(14,0), 'USD'::character varying(3))::money_value, ROW(COALESCE(sum(pi.metal_balance) FILTER (WHERE pi.metal_balance_currency::text = 'EUR'::text), 0.0)::numeric(14,0), 'EUR'::character varying(3))::money_value] AS balances,
        COALESCE(sum(pa.allocated) FILTER (WHERE pa.allocated_currency::text = 'INR'::text), 0.0) AS cash_received,
        COALESCE(sum(pa.allocated) FILTER (WHERE pa.allocated_currency::text = 'USD'::text), 0.0) AS gold_received,
        COALESCE(sum(pa.allocated) FILTER (WHERE pa.allocated_currency::text = 'EUR'::text), 0.0) AS silver_received,
        ARRAY[ROW(COALESCE(sum(pa.allocated) FILTER (WHERE pa.allocated_currency::text = 'INR'::text), 0.0)::numeric(14,0), 'INR'::character varying(3))::money_value, ROW(COALESCE(sum(pa.allocated) FILTER (WHERE pa.allocated_currency::text = 'USD'::text), 0.0)::numeric(14,0), 'USD'::character varying(3))::money_value, ROW(COALESCE(sum(pa.allocated) FILTER (WHERE pa.allocated_currency::text = 'EUR'::text), 0.0)::numeric(14,0), 'EUR'::character varying(3))::money_value] AS received
    FROM sales_invoice
     JOIN sales_invoiceitem pi ON pi.invoice_id = sales_invoice.id
     LEFT JOIN sales_receiptallocation pa ON pa.invoice_id = sales_invoice.id
    GROUP BY sales_invoice.id;"""

    voucher = models.OneToOneField(
        "sales.Invoice",
        on_delete=models.DO_NOTHING,
        primary_key=True,
        related_name="sale_balance",
    )
    cash_balance = models.DecimalField(max_digits=14, decimal_places=3)
    gold_balance = models.DecimalField(max_digits=14, decimal_places=3)
    silver_balance = models.DecimalField(max_digits=14, decimal_places=3)
    balances = ArrayField(MoneyValueField(null=True, blank=True))
    cash_received = models.DecimalField(max_digits=14, decimal_places=3)
    gold_received = models.DecimalField(max_digits=14, decimal_places=3)
    silver_received = models.DecimalField(max_digits=14, decimal_places=3)
    received = ArrayField(MoneyValueField(null=True, blank=True))

    class Meta:
        managed = False
        db_table = "sale_balance"

    def __str__(self):
        return f"Balance:{Balance([self.balances]) - Balance([self.received])}"

    def balance(self):
        return Balance([self.balances]) - Balance([self.received])
