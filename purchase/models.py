from datetime import date, timedelta

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
from django.db.models import F, Q, Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from moneyed import Money

from contact.models import Customer
from dea.models import Journal, JournalTypes
from invoice.models import PaymentTerm
from product.attributes import get_product_attributes_data
from product.models import (Attribute, ProductVariant, Stock, StockLot,
                            StockTransaction)


# if not posted : delete/edit
#  if posted : !edit
#  delete any time
class PurchaseQueryset(models.QuerySet):
    def posted(self):
        return self.filter(posted=True)

    def unposted(self):
        return self.filter(posted=False)

    def gst(self):
        return self.filter(is_gst=True)

    def non_gst(self):
        return self.filter(is_gst=False)

    def total(self):
        return self.aggregate(
            cash=Sum("balance", filter=Q(balancetype="INR")),
            gold=Sum("balance", filter=Q(balancetype="USD")),
            silver=Sum("balance", filter=Q(balancetype="AUD")),
        )

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


class Invoice(models.Model):
    # Fields
    created = models.DateTimeField(default=timezone.now, db_index=True)
    updated = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="purchased",
    )
    rate = models.DecimalField(max_digits=10, decimal_places=3)
    is_gst = models.BooleanField(default=False)
    posted = models.BooleanField(default=False)
    gross_wt = models.DecimalField(max_digits=14, decimal_places=4, default=0.0)
    net_wt = models.DecimalField(max_digits=14, decimal_places=4, default=0.0)
    total = models.DecimalField(max_digits=14, decimal_places=4, default=0.0)
    discount = models.DecimalField(max_digits=14, decimal_places=4, default=0.0)
    balance = models.DecimalField(max_digits=14, decimal_places=4, default=0.0)

    class BType(models.TextChoices):
        CASH = (
            "INR",
            _("Cash"),
        )
        GOLD = (
            "USD",
            _("Gold"),
        )
        SILVER = "AUD", _("Silver")

    metal_choices = (("Gold", "Gold"), ("Silver", "Silver"))
    status_choices = (
        ("Paid", "Paid"),
        ("PartiallyPaid", "PartiallyPaid"),
        ("Unpaid", "Unpaid"),
    )
    status = models.CharField(max_length=15, choices=status_choices, default="Unpaid")
    balancetype = models.CharField(
        max_length=30, choices=BType.choices, default=BType.CASH
    )
    metaltype = models.CharField(max_length=30, choices=metal_choices, default="Gold")
    due_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    # Relationship Fields
    supplier = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="purchases"
    )
    term = models.ForeignKey(
        PaymentTerm,
        on_delete=models.SET_NULL,
        related_name="purchase_term",
        blank=True,
        null=True,
    )
    journals = GenericRelation(Journal, related_query_name="purchase_doc")
    stock_txns = GenericRelation(StockTransaction)
    objects = PurchaseQueryset.as_manager()

    class Meta:
        ordering = (
            "id",
            "created",
        )

    def __str__(self):
        return f"{self.id}"

    def get_absolute_url(self):
        return reverse("purchase:purchase_invoice_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("purchase:purchase_invoice_update", args=(self.pk,))

    def get_next(self):
        return Invoice.objects.filter(id__gt=self.id).order_by("id").first()

    def get_previous(self):
        return Invoice.objects.filter(id__lt=self.id).order_by("id").last()

    def get_gross_wt(self):
        return self.purchaseitems.aggregate(t=Sum("weight"))["t"]

    def get_net_wt(self):
        return self.purchaseitems.aggregate(t=Sum("net_wt"))["t"]

    # @property
    # def outstanding_balance(self):
    #     return self.balance - self.total_allocated_amount

    @classmethod
    def with_outstanding_balance(cls):
        return cls.objects.annotate(
            total_allocated_amount=Sum("paymentallocation__allocated_amount")
        ).annotate(outstanding_balance=F("balance") - F("total_allocated_amount"))

    # overdue_invoices = Invoice.with_outstanding_balance().filter(outstanding_balance__gt=0, due_date__lt=date.today())

    def get_total_balance(self):
        return self.purchaseitems.aggregate(t=Sum("total"))["t"]

    def get_allocations(self):
        paid = self.paymentallocation_set.aggregate(t=Sum("allocated_amount"))
        return paid["t"]

    @property
    def overdue_days(self):
        return (timezone.now().date() - self.due_date).days

    def get_balance(self):
        if self.get_total_payments() != None:
            return self.balance - self.get_total_payments()
        return self.total

    def save(self, *args, **kwargs):
        self.due_date = self.created + timedelta(days=self.term.due_days)
        # if self.is_gst:
        #     self.total += self.get_gst()
        self.total = self.balance + self.get_gst()

        super(Invoice, self).save(*args, **kwargs)

    def get_gst(self):
        return (self.balance * 3) / 100 if self.is_gst else 0

    @transaction.atomic()
    def post(self):
        if not self.posted:
            try:
                self.supplier.account
            except self.supplier.account.DOESNOTEXIST:
                self.supplier.save()

            jrnl = Journal.objects.create(
                journal_type=JournalTypes.PJ,
                content_object=self,
                desc="purchase",
                contact=self.supplier,
            )

            inv = "GST INV" if self.is_gst else "Non-GST INV"
            money = Money(self.balance, self.balancetype)
            tax = Money(self.get_gst(), "INR")
            lt = [
                {"ledgerno": "Sundry Creditors", "ledgerno_dr": inv, "amount": money},
                {
                    "ledgerno": "Sundry Creditors",
                    "ledgerno_dr": "Input Igst",
                    "amount": tax,
                },
            ]
            at = [
                {
                    "ledgerno": "Sundry Creditors",
                    "xacttypecode": "Dr",
                    "xacttypecode_ext": "CRPU",
                    "account": self.supplier.account,
                    "amount": money + tax,
                }
            ]
            jrnl.transact(lt, at)
            for i in self.purchaseitems.all():
                i.post(jrnl)
            self.posted = True
            self.save(update_fields=["posted"])

    @transaction.atomic()
    def unpost(self):
        if self.posted:
            last_jrnl = self.journals.latest()
            jrnl = Journal.objects.create(
                content_object=self,
                desc="purchase revert",
                contact=self.supplier,
                jouranl_type=JournalTypes.PJ,
            )
            jrnl.untransact(last_jrnl)
            for i in self.purchaseitems.all():
                i.unpost(jrnl)
            self.posted = False
            self.save(update_fields=["posted"])


class InvoiceItem(models.Model):
    # Fields
    quantity = models.IntegerField()
    weight = models.DecimalField(max_digits=10, decimal_places=3)
    touch = models.DecimalField(max_digits=10, decimal_places=3)
    net_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=3, blank=True)
    is_return = models.BooleanField(default=False, verbose_name="Return")
    makingcharge = models.DecimalField(
        max_digits=10, decimal_places=3, blank=True, null=True
    )
    # Relationship Fields
    product = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name="products"
    )
    invoice = models.ForeignKey(
        "purchase.Invoice", on_delete=models.CASCADE, related_name="purchaseitems"
    )

    class Meta:
        ordering = ("-pk",)

    def __str__(self):
        return "%s" % self.pk

    def get_absolute_url(self):
        return reverse("purchase:purchase_invoiceitem_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("purchase:purchase_invoiceitem_update", args=(self.pk,))

    def get_nettwt(self):
        return (self.weight * self.touch) / 100

    @transaction.atomic()
    def post(self, journal):
        """
        if not return item create/add a stocklot then transact,
        if return item then remove the lot from stocklot"""
        if not self.is_return:
            stock, created = Stock.objects.get_or_create(variant=self.product)
            stock_lot = StockLot.objects.create(
                variant=self.product,
                stock=stock,
                wt=self.weight,
                qty=self.quantity,
                purchase_touch=self.touch,
                purchase_rate=self.invoice.rate,
                purchase=self.invoice,
            )
            stock_lot.transact(
                weight=self.weight,
                quantity=self.quantity,
                journal=journal,
                movement_type="P",
            )

        else:
            lot = StockLot.objects.get(stock__variant=self.product)
            lot.transact(
                journal=journal,
                weight=self.weight,
                quantity=self.quantity,
                movement_type="PR",
            )

    @transaction.atomic()
    def unpost(self, journal):
        """
        add lot back to stock lot if item is_return,
        remove lot from stocklot if item is not return item"""
        if self.is_return:
            self.product.stock_lots.get(variant=self.product).transact(
                journal=journal,
                weight=self.weight,
                quantity=self.quantity,
                movement_type="P",
            )
        else:
            self.product.stock_lots.get(variant=self.product).transact(
                journal=journal,
                weight=self.weight,
                quantity=self.quantity,
                movement_type="PR",
            )


class Payment(models.Model):
    # Fields
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now_add=True, editable=False)
    created_by = models.ForeignKey(
        "users.CustomUser", on_delete=models.CASCADE, null=True, blank=True
    )

    class BType(models.TextChoices):
        CASH = (
            "INR",
            _("Cash"),
        )
        GOLD = (
            "USD",
            _("Gold"),
        )
        SILVER = "AUD", _("Silver")

    type = models.CharField(
        max_length=30,
        verbose_name="Currency",
        choices=BType.choices,
        default=BType.CASH,
    )
    weight = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    touch = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    rate = models.IntegerField(default=0)
    total = models.DecimalField(max_digits=10, decimal_places=3)
    description = models.TextField(max_length=100)
    status_choices = (
        ("Allotted", "Allotted"),
        ("Partially Allotted", "PartiallyAllotted"),
        ("Unallotted", "Unallotted"),
    )
    status = models.CharField(
        max_length=18, choices=status_choices, default="Unallotted"
    )
    posted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    journals = GenericRelation(Journal, related_query_name="payment_doc")
    # Relationship Fields
    supplier = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="payments"
    )
    invoices = models.ManyToManyField(Invoice, through="PaymentAllocation")

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return "%s" % self.id

    def get_absolute_url(self):
        return reverse("purchase:purchase_payment_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("purchase:purchase_payment_update", args=(self.pk,))

    def update_status(self):
        # total_allotted = self.get_line_totals()
        total_allotted = (
            self.paymentallocation_set.aggregate(t=Sum("allocated_amount"))["t"]
            if self.paymentallocation_set.exists()
            else 0
        )
        print(f"total_allotted : {total_allotted}")

        if total_allotted == self.total:
            self.status = "Allotted"
        else:
            self.status = "Unallotted"
        self.save()

    def allot(self):
        if self.posted:
            print(f"allotting payment {self.id} type:{self.type} amount{self.total}")
            invpaid = 0 if self.amount_allotted() is None else self.amount_allotted()
            print(f" invpaid : {invpaid}")
            remaining_amount = self.total - invpaid
            print(f"remaining : {remaining_amount}")
            try:
                invtopay = (
                    Invoice.objects.filter(
                        supplier=self.supplier,
                        balancetype=self.type,
                        posted=True,
                        balance__gte=0,
                    )
                    .exclude(status="Paid")
                    .order_by("created")
                )
            except IndexError:
                invtopay = None
            print(f" invtopay :{invtopay}")

            for i in invtopay:
                print(f"i:{i} bal:{i.get_balance()}")
                if remaining_amount <= 0:
                    break
                bal = i.get_balance()
                if remaining_amount >= bal:
                    remaining_amount -= bal
                    PaymentAllocation.objects.create(
                        payment=self, invoice=i, allocated_amount=bal
                    )
                    i.status = "Paid"
                else:
                    PaymentAllocation.objects.create(
                        payment=self, invoice=i, allocated_amount=remaining_amount
                    )
                    i.status = "PartiallyPaid"
                    remaining_amount = 0
                i.save()
            print("allotted payment")
            self.update_status()
        else:
            raise Exception("Payment not posted")

    def deallot(self):
        self.paymentallocation_set.all().delete()
        self.update_status()

    def post(self):
        if not self.posted:
            jrnl = Journal.objects.create(
                contact=self.supplier,
                journal_type=JournalTypes.PY,
                content_object=self,
                desc="payment",
            )

            money = Money(self.total, self.type)
            lt = [
                {"ledgerno": "Cash", "ledgerno_dr": "Sundry Creditors", "amount": money}
            ]
            at = [
                {
                    "ledgerno": "Sundry Creditors",
                    "xacttypecode": "Dr",
                    "xacttypecode_ext": "PYT",
                    "account": self.supplier.account,
                    "amount": money,
                }
            ]
            jrnl.transact(lt, at)
            self.posted = True
            self.save(update_fields=["posted"])

    def unpost(self):
        if self.posted:
            last_jrnl = self.journals.latest()
            jrnl = Journal.objects.create(
                content_object=self,
                desc="payment - unpost",
                contact=self.supplier,
            )
            jrnl.untransact(last_jrnl)
            self.deallot()
            self.posted = False
            self.save(update_fields=["posted"])

    def amount_allotted(self):
        return (
            self.paymentallocation_set.aggregate(t=Sum("allocated_amount"))["t"]
            if self.paymentallocation_set.exists()
            else 0
        )

    def allocate(self):
        # get all unpaid invoices associated with this payment's customer
        unpaid_invoices = (
            Invoice.with_outstanding_balance()
            .filter(
                supplier=self.supplier,
                # paid=False,
                balancetype=self.type,
                posted=True,
                balance__gte=0,
                outstanding_balance__gt=0,
            )
            .exclude(status="Paid")
            .order_by("created")
        )

        # iterate over the unpaid invoices and allocate payment in order
        amount_remaining = self.total
        for invoice in unpaid_invoices:
            if amount_remaining <= 0:
                break

            # calculate the amount to allocate to this invoice
            amount_due = invoice.outstanding_balance
            print(f"amount_due:{amount_due}")
            print(f"amount_remaining:{amount_remaining}")
            amount_to_allocate = min(amount_due, amount_remaining)

            # create a PaymentAllocation object for this invoice and payment
            allocation = PaymentAllocation.objects.create(
                payment=self, invoice=invoice, allocated_amount=amount_to_allocate
            )

            # update the amount remaining to allocate
            amount_remaining -= amount_to_allocate

        # mark the payment as fully allocated if there is no amount remaining
        if amount_remaining <= 0:
            self.status = "Allotted"
            self.save()
        self.update_status()


class PaymentAllocation(models.Model):
    created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    allocated_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return "%s" % self.id

    def get_absolute_url(self):
        return reverse("purchase_paymentallocated_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("purchase_paymentallocated_update", args=(self.pk,))


"""
    This is a view that is used to get the outstanding balance of an invoice.
    SQL:
        CREATE VIEW invoice_payment_view AS 
        SELECT invoice.id, invoice.invoice_number, invoice.total_amount, 
            COALESCE(SUM(payment_allocation.allocated_amount), 0) AS amount_allocated, 
            COALESCE(SUM(payment.amount), 0) AS amount_paid 
        FROM invoice 
        LEFT JOIN payment_allocation ON invoice.id = payment_allocation.invoice_id 
        LEFT JOIN payment ON payment_allocation.payment_id = payment.id 
        GROUP BY invoice.id;

    invoice_payments = InvoicePaymentView.objects.all()
    for invoice in invoice_payments:
        print(f"Invoice #{invoice.invoice_number}: Total amount: {invoice.total_amount}, Amount paid: {invoice.amount_paid}, Amount allocated: {invoice.amount_allocated}, Outstanding balance: {invoice.outstanding_balance}")

"""


class InvoicePaymentView(models.Model):
    invoice_number = models.CharField(max_length=50)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_allocated = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def outstanding_balance(self):
        return self.total_amount - self.amount_paid

    @classmethod
    def get_queryset(cls):
        return cls.objects.annotate(
            amount_allocated=Sum("invoice_payments__allocated_amount")
        )

    class Meta:
        managed = False
        db_table = "invoice_payment_view"
