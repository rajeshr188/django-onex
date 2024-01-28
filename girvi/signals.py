from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from dea.models import JournalEntry
from girvi.models import Adjustment, Loan, LoanItem, Release


@receiver(post_save, sender=LoanItem)
@receiver(post_delete, sender=LoanItem)
def update_loan(sender, instance, **kwargs):
    loan = instance.loan
    loan_items = LoanItem.objects.filter(loan=loan)
    loan.loanamount = sum(item.loanamount for item in loan_items)
    loan.itemdesc = ", ".join([item.itemdesc for item in loan.loanitems.all()])
    loan.interest = sum(item.interest for item in loan_items)
    loan.save()


# @receiver(post_save, sender=Loan)
# @receiver(post_save, sender=Adjustment)
# @receiver(post_save, sender=Release)
def create_journal(sender, instance, created, **kwargs):
    # lt, at = instance.loan.get_transactions()
    if created:
        # print("newly created journal")
        
        instance.create_transactions()
    else:
        # print("existing journal:appending txns")
        # lj, aj = instance.get_journals()
        # print(f"in signalls lt:{lt}")
       
        instance.reverse_transactions()
        instance.create_transactions()
    return instance
