from django.db.models.signals import (post_delete, post_save, pre_delete,
                                      pre_save)
from django.dispatch import receiver

from girvi.models import Loan, LoanItem


@receiver(post_save, sender=LoanItem)
@receiver(pre_delete, sender=LoanItem)
def update_loan(sender, instance, **kwargs):
    loan = instance.loan
    loan_items = LoanItem.objects.filter(loan=loan)
    loan.loanamount = sum(item.loanamount for item in loan_items)
    loan.itemdesc = ", ".join([item.itemdesc for item in loan.loanitems.all()])
    loan.interest = sum(item.interest for item in loan_items)
    loan.save()
