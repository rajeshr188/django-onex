from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
from django.db.models import Sum
from django.urls import reverse

from approval.models import ApprovalLine
from contact.models import Customer
from dea.models import Journal,JournalEntry #, JournalTypes
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


class Return(Journal):
    
    contact = models.ForeignKey(
        Customer, related_name="approval_returns", on_delete=models.CASCADE
    )
    total_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    total_qty = models.IntegerField(default=0)
  
    def __str__(self):
        return f"Return #{self.id}"

    def get_absolute_url(self):
        return reverse("approval:approval_return_detail", args=(self.pk,))

    def get_total_qty(self):
        return self.returnitem_set.aggregate(t=Sum("quantity"))["t"]

    def get_total_wt(self):
        return self.returnitem_set.aggregate(t=Sum("weight"))["t"]
    
    def get_items(self):
        return self.return_items.all()


class ReturnItem(models.Model):
    return_obj = models.ForeignKey(
                    Return, 
                    on_delete=models.CASCADE,
                    related_name="return_items")
    line_item = models.ForeignKey(
                    ApprovalLine, 
                    on_delete=models.CASCADE, 
                    related_name="return_items"
    )
    quantity = models.IntegerField(default=0)
    weight = models.DecimalField(max_digits=10, decimal_places=3, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.quantity} x {self.line_item.product}"

    def get_absolute_url(self):
        return reverse("approval:approval_returnitem_detail", args=(self.pk,))

    def get_hx_edit_url(self):
        kwargs = {"return_pk": self.return_obj.id, "pk": self.pk}
        return reverse("approval:approval_returnitem_update", kwargs=kwargs)

    @transaction.atomic
    def post(self):
        journal_entry = self.return_obj.get_journal_entry()
        self.line_item.product.transact(self.weight, self.quantity, journal_entry, "AR")
        self.line_item.update_status()

    @transaction.atomic
    def unpost(self):
        journal_entry = self.return_obj.get_journal_entry()
        self.line_item.product.transact(self.weight, self.quantity, journal, "A")
        self.line_item.update_status()