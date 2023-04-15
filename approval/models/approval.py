from django.contrib.contenttypes.fields import GenericRelation
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

If the approval is closed, the approval should be flagged as closed and no further changes should be allowed.

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
    # calculated fields need to be stored?
    total_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    total_qty = models.IntegerField(default=0)

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

    """
    called when an return item is created with a line item referencing this approval/approvalline,
     otherwise called from approvalline.save() ,by default stus is pending
     """
    def update_status(self):
        print("in approval update_Status")

        # for i in self.items.all():
        #     i.update_status()
        if any(i.status in ['Pending','Partially Returned'] for i in self.items.all()):
            self.status = "Pending"
        else:
            self.status = "Complete"
        self.save()

    # called when an invoice cis created with a line item referencing this approval/approvalline
    def update_billed_status(self):
        if any(i.status == "Billed" for i in self.items.all()):
            self.is_billed = True
        else:
            self.is_billed = False
        self.save()

    def get_total_qty(self):
        return self.items.aggregate(t=Sum("quantity"))["t"]

    def get_total_wt(self):
        return self.items.aggregate(t=Sum("weight"))["t"]

    def update_total(self):
        self.total_wt = self.get_total_wt()
        self.total_qty = self.get_total_wt()
        self.update_billed_status()
        self.save()


class ApprovalLine(models.Model):
    product = models.ForeignKey(
        StockLot, related_name="lineitems", on_delete=models.CASCADE
    )
    quantity = models.IntegerField(default=0)
    weight = models.DecimalField(max_digits=10, decimal_places=3, default=0.0)
    touch = models.DecimalField(max_digits=10, decimal_places=3, default=0.0)

    approval = models.ForeignKey(
        Approval, on_delete=models.CASCADE, related_name="items"
    )
    # newly added based on chatgpt suggestion
    invoice = models.ForeignKey(
        "sales.Invoice", on_delete=models.CASCADE, null=True, blank=True
    )

    status = models.CharField(
        max_length=30,
        # onapproval or returned or billed
        choices=(
            ("Pending", "Pending"),
            ("Partially Returned", "Partially Returned"),
            ("Returned", "Returned"),
            ("Billed", "Billed"),
        ),
        default="Pending",
        blank=True,
    )
    journal = GenericRelation(Journal, related_query_name="approval_lineitems")

    class Meta:
        ordering = ("approval",)

    def __str__(self):
        return f"{self.id} - {self.product.barcode}"

    def get_absolute_url(self):
        return reverse("approval:approval_approvalline_detail", args=(self.pk,))

    def get_hx_edit_url(self):
        kwargs = {"approval_pk": self.approval.id, "pk": self.pk}
        return reverse("approval:approval_approvalline_update", kwargs=kwargs)

    def balance(self):
        return (
            self.weight
            - self.approvallinereturn_set.aggregate(
                t=Sum("weight")
            )["t"]
        )

    # called when return item is created otherwise status is pending
    def update_status(self):
        ret = {"qty": 0, "wt": 0}
        if self.return_items.exists():
            ret = self.return_items.aggregate(
                qty=Sum("quantity"), wt=Sum("weight")
            )
            print(ret)
        if self.quantity - ret["qty"] > 0 and self.weight - ret["wt"] > 0:
            self.status = "Partially Returned"
            print("partially returned")
        elif self.quantity - ret["qty"] == 0 and self.weight - ret["wt"] == 0:
            self.status = "Returned"
            print("returned")
        else:
            self.status = "Pending"
            print("pending")
        self.save()
        self.approval.update_status()

    def get_returned_qty(self):
        # return the ReturnItem quanitty for thisapprovalline
        return self.returnitem_set.aggregate(Sum("quantity"))["quantity_sum"]

    def create_journal(self):
        jrnl = Journal.objects.create(
            journal_type="SJ",
            content_object=self,
            desc=f"Approval {self.approval.id} - {self.product.barcode}",
        )
        return jrnl

    def get_journal(self):
        return self.journal.first() if self.journal.exists() else create_journal()

    def delete_journals(self):
        # delete journals for this approvalline
        pass

    def post(self, journal):
        self.product.transact(
            weight=self.weight,
            quantity=self.quantity,
            journal=self.get_journal(),
            movement_type="A",
        )

    def unpost(self, journal):
        # generally an approval/approval line shouldnt be edited onece the items are returned.
        # for i in self.returnitem_set.all():
        #     i.unpost(journal)
        #     i.delete()
        self.product.transact(self.weight, self.quantity, journal, "AR")
