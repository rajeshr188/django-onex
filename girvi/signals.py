from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver

from girvi.models import Loan, LoanItem


@receiver([pre_delete, post_save], sender=LoanItem)
def update_loan(sender, instance, **kwargs):
    loan = instance.loan
    loan_items = LoanItem.objects.filter(loan=loan)
    loan.loan_amount = sum(item.loanamount for item in loan_items)
    loan.item_desc = ", ".join([item.itemdesc for item in loan.loanitems.all()])
    loan.interest = sum(item.interest for item in loan_items)
    loan.save()
