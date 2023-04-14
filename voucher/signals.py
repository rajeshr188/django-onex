from django.db.models.signals import post_save
from dea.models import Journal
from django.dispatch import receiver

# @receiver(post_save, sender=Loan)
def create_journal(sender, instance, created, **kwargs):
    lt,at = instance.get_transactions()
    if created:
        print("newly created journal")
        lj,aj = instance.create_journals()
        lj.transact(lt)
        aj.transact(at)
    else:
        print("existing journal:appending txns")
        lj,aj = instance.get_journals()
        print(f"in signalls lt:{lt}")
        lj.untransact(lt)
        aj.untransact(at)
        lj.transact(lt)
        aj.transact(at)
    return instance