from django.utils import timezone
from dateutil import relativedelta
from girvi.models import Loan
import tablib

def calculate_score(contact):
    l = Loan.objects.filter(customer = contact)
    for i in l:
        contact.contactscore_set.create(score=5, desc='loan created')
        if i.is_released:
                delta = relativedelta.relativedelta(
                    i.release.created, i.created)
                no_of_months = delta.years * 12 + delta.months
                if no_of_months <= 3:
                    contact.contactscore_set.create(
                        score=5, desc='released < 3 mos')
                elif no_of_months <= 6 and no_of_months > 3:
                    contact.contactscore_set.create(
                        score=4, desc='released >3<6 mos')
                elif no_of_months <= 9 and no_of_months > 6:
                    contact.contactscore_set.create(
                        score=3, desc='released >6<9 mos')
                elif no_of_months <= 12 and no_of_months > 9:
                    contact.contactscore_set.create(
                        score=2, desc='released >9<12 mos')
                elif no_of_months > 12:
                    contact.contactscore_set.create(
                        score=1, desc='released >12 mos')
        else:
            delta = relativedelta.relativedelta(
                timezone.now(), i.created)
            no_of_years = delta.years
            if no_of_years > 1:
                contact.contactscore_set.create(
                    score=-5, desc='unreleased > 1 year')


def eliminate_dups(ds):
    seen = set()
    uniq = []

    for row in ds:
        if not(tuple((row[4], row[13], row[14])) in seen or seen.add(tuple((row[4], row[13], row[14])))):
           uniq.append(row)

        else:
            row_l = list(row)
            row_l[4] = row_l[4] + ' +'
            row_l[2] = row_l[1]
            uniq.append(tuple(row_l))
    headers = ('id', 'created', 'updated', 'created_by', 'name', 'firstname', 'lastname', 'gender', 'religion',
                        'pic','phonenumber', 'Address', 'type', 'relatedas', 'relatedto', 'area', 'active')
    ds = tablib.Dataset(*uniq,headers = headers)

    return ds

def remove_dups(ds):
    seen = set()
    return [row for row in ds if not (tuple((row[3], row[12], row[13])) in seen or seen.add(tuple((row[3], row[12], row[13]))))]

# def setrank():
#     c_score_list = 
        
