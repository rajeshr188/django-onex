from dateutil import relativedelta
from django.utils import timezone

from girvi.models import Loan


def calculate_score(contact):
    l = Loan.objects.filter(customer=contact)
    for i in l:
        contact.contactscore_set.create(score=5, desc="loan created")
        if i.is_released:
            delta = relativedelta.relativedelta(i.release.created, i.created)
            no_of_months = delta.years * 12 + delta.months
            if no_of_months <= 3:
                contact.contactscore_set.create(score=5, desc="released < 3 mos")
            elif no_of_months <= 6 and no_of_months > 3:
                contact.contactscore_set.create(score=4, desc="released >3<6 mos")
            elif no_of_months <= 9 and no_of_months > 6:
                contact.contactscore_set.create(score=3, desc="released >6<9 mos")
            elif no_of_months <= 12 and no_of_months > 9:
                contact.contactscore_set.create(score=2, desc="released >9<12 mos")
            elif no_of_months > 12:
                contact.contactscore_set.create(score=1, desc="released >12 mos")
        else:
            delta = relativedelta.relativedelta(timezone.now(), i.created)
            no_of_years = delta.years
            if no_of_years > 1:
                contact.contactscore_set.create(score=-5, desc="unreleased > 1 year")


# def setrank():
#     c_score_list =
