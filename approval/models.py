from django.db import models, transaction
from django.db.models import Sum
from django.urls import reverse

from contact.models import Customer
from dea.models import Journal
from product.models import StockLot

"""
When an approval voucher is created, the stock items that are being approved for release to a contact should be recorded in the database or inventory management system, along with the contact's information.

When the approved stock items are released to the contact, they should be recorded as being moved out of the approval area and into the possession of the contact.

If the contact returns some or all of the approved stock items, those items should be recorded as being returned to the approval area.

When the approval is complete and all approved stock items have been returned, the approval should be closed.

If any stock items were approved for release but not returned, those items should be flagged for invoicing.

When the invoice is created, the stock items that were approved but not returned should be included on the invoice, along with the appropriate billing information.

If any changes are made to the approval, return, or invoice, those changes should be recorded in the database or inventory management system, along with a timestamp and the user who made the changes.
"""


# Create your models here.
class Approval(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        "users.CustomUser", on_delete=models.CASCADE, null=True, blank=True
    )
    contact = models.ForeignKey(
        Customer, related_name="contact", on_delete=models.CASCADE
    )
    total_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    total_qty = models.IntegerField(default=0)
    posted = models.BooleanField(default=False)
    # is_billed is status now
    is_billed = models.BooleanField(default=False)
    status = models.CharField(
        max_length=10,
        choices=(
            ("Pending", "Pending"),
            ("Complete", "Complete"),
            ("Billed", "Billed"),
        ),
        default="Pending",
    )

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"{self.id}"

    def get_absolute_url(self):
        return reverse("approval:approval_approval_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("approval:approval_approval_update", args=(self.pk,))

    @transaction.atomic()
    def post(self):
        if not self.posted:
            journal = Journal.objects.create(
                contact=self.contact,
                journal_type="AP",
                content_object=self,
                desc=f"Approval {self.id}",
            )
            for i in self.items.all():
                i.post(journal=journal)
        self.posted = True
        self.save(update_fields=["posted"])

    @transaction.atomic()
    def unpost(self):
        # if is billed cant unpost
        if self.posted and not self.is_billed:
            # last_jrnl = self.journals.latest()
            jrnl = Journal.objects.create(
                content_object=self,
                journal_type="AP",
                contact=self.contact,
                desc="approval revert",
            )
            for i in self.items.all():
                i.unpost(jrnl)
            self.posted = False
            self.save(update_fields=["posted"])

    def update_status(self):
        print("in approval update_Status")
        for i in self.items.all():
            print(f"{i}-{i.status} ")
        if any(i.status == "Pending" for i in self.items.all()):
            self.status = "Pending"
        else:
            self.status = "Complete"
        self.save()


# rename to lineitem tobe referenced by return line and invoice line
class ApprovalLine(models.Model):
    product = models.ForeignKey(
        StockLot, related_name="approval_lineitems", on_delete=models.CASCADE
    )
    quantity = models.IntegerField(default=0)
    weight = models.DecimalField(max_digits=10, decimal_places=3, default=0.0)
    touch = models.DecimalField(max_digits=10, decimal_places=3, default=0.0)

    approval = models.ForeignKey(
        Approval, on_delete=models.CASCADE, related_name="items"
    )
    # newly added based on chatgpt suggestion
    # invoice = models.ForeignKey('sales.Invoice', on_delete=models.CASCADE, null=True, blank=True)

    status = models.CharField(
        max_length=30,
        choices=(
            ("Pending", "Pending"),
            ("Returned", "Returned"),
            ("Billed", "Billed"),
        ),
        default="Pending",
        blank=True,
    )

    class Meta:
        ordering = ("approval",)

    def __str__(self):
        return f"{self.id}"

    def balance(self):
        return (
            self.weight
            - self.approvallinereturn_set.filter(posted=True).aggregate(
                t=Sum("weight")
            )["t"]
        )

    def post(self, journal):
        self.product.transact(
            weight=self.weight,
            quantity=self.quantity,
            journal=journal,
            movement_type="A",
        )

    def unpost(self, journal):
        for i in self.approvallinereturn_set.all():
            i.unpost(journal)
            i.delete()
        self.product.transact(self.weight, self.quantity, journal, "AR")

    def update_status(self):
        ret = self.approvallinereturn_set.filter(posted=True).aggregate(
            qty=Sum("quantity"), wt=Sum("weight")
        )
        if self.quantity == ret["qty"] and self.weight == ret["wt"]:
            self.status = "Returned"
        else:
            self.status = "Pending"
        self.save()
        self.approval.update_status()


# rename to Return for better clarity
class ApprovalLineReturn(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        "users.CustomUser", on_delete=models.CASCADE, null=True, blank=True
    )
    line = models.ForeignKey(ApprovalLine, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    weight = models.DecimalField(max_digits=10, decimal_places=3, default=0.0)
    posted = models.BooleanField(default=False)

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return f"{self.line.product}"

    def post(self, journal):
        if not self.posted:
            self.line.product.transact(self.weight, self.quantity, journal, "AR")
            self.posted = True
            self.save(update_fields=["posted"])
            self.line.update_status()

    def unpost(self):
        if self.posted:
            self.line.product.transact(self.weight, self.quantity, journal, "A")
            self.posted = False
            self.save(update_fields=["posted"])
            self.line.update_status()


class Return(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        "users.CustomUser", on_delete=models.CASCADE, null=True, blank=True
    )
    contact = models.ForeignKey(
        Customer, related_name="approval_returns", on_delete=models.CASCADE
    )
    total_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    total_qty = models.IntegerField(default=0)
    posted = models.BooleanField(default=False)

    def __str__(self):
        return f"Return #{self.id} for {self.contact}"


class ReturnLineItem(models.Model):
    return_obj = models.ForeignKey(Return, on_delete=models.CASCADE)
    line_item = models.ForeignKey(ApprovalLine, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    weight = models.DecimalField(max_digits=10, decimal_places=3, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.quantity} x {self.line_item.product.name} ({self.line_item.price} each)"
