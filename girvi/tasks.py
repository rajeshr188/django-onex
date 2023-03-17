from __future__ import absolute_import, unicode_literals

import datetime

from celery import shared_task
from celery.utils.log import get_task_logger

from .msg import notify_msg

logger = get_task_logger(__name__)

# import datetime
# @shared_task(name="twilio status")
# def notify(name="twilio_up"):

#     client = Client(env('TWILIO_ACCOUNT_SID'), env('TWILIO_AUTH_TOKEN'))

#     message = client.messages.create(
#                                 body=f'J Champalal PawnBroker:\
#                                          {datetime.datetime.now()}you have loans that are overdue,pls contact: 7904286981',
#                                 from_=env('TWILIO_NUMBER'),
#                                 to='+917598260045'
#                             )

#     return message.sid


# this runs at the start of everymonth
@shared_task(name="pending_loans")
def notify_pending_loans():
    # Get all the users who have pending loans
    unreleased_loans = Loan.unreleased.order_by("customer")
    customers_with_pending_loans = Customer.objects.filter(
        loan__in=unreleased_loans
    ).distinct()

    # Iterate over each user and send them a notification email
    for customer in customers_with_pending_loans:
        # Get the user's pending loans
        pending_loans = pending_loans.filter(customer=customer)

        # Compose the message
        message = f"Dear {customer.name},\n\n"
        message += f"You have {pending_loans.count()} pending loan(s) as of {datetime.now().strftime('%Y-%m-%d')}."
        message += (
            "Please make a payment as soon as possible to avoid additional fees.\n\n"
        )
        message += "Thank you for your cooperation.\n\n"
        message += "Best regards,\nThe Loan Department"
        notify_msg(number=customer.contactno.first().phone_number, content=message)


# this runs everyday selecting the loans that were created on this day of month and notify users the no of months
@shared_task(name="interest_overdue_permonth")
def notify_interest_overdue():
    unreleased_loans = Loan.unreleased.filter(
        created__day=datetime.datetime.date().today.day
    ).order_by("customer")
    logger.info("msg")
    customers_with_pending_loans = Customer.objects.filter(
        loan__in=unreleased_loans
    ).distinct()

    # Iterate over each user and send them a notification
    for customer in customers_with_pending_loans:
        # Get the user's pending loans
        pending_loans = pending_loans.filter(customer=customer)

        # Compose the message
        message = f"Dear {customer.name},\n\n"
        # message += f"You have {pending_loans.count()} pending loan(s) as of {datetime.now().strftime('%Y-%m-%d')}."
        for i in pending_loans:
            message += f"your loan {i.loanid} is completing {i.noofmonths|add:'1'}"
        message += "Please make a interest payment as soon as possible to avoid additional fees.\n\n"
        message += "Thank you for your cooperation.\n\n"
        message += "Best regards,\nThe Loan Department"
        notify_msg(number=customer.contactno.first().phone_number, content=message)


@shared_task(name="one_year_reminder")
def notify_Loan_reminder():
    unreleased_loans = Loan.unreleased.filter(
        created__day=datetime.datetime.date.today().day,
        created__month=datetime.datetime.date.today().month,
    ).order_by("customer")
    logger.info("msg")
    customers_with_pending_loans = Customer.objects.filter(
        loan__in=unreleased_loans
    ).distinct()

    # Iterate over each user and send them a notification
    for customer in customers_with_pending_loans:
        # Get the user's pending loans
        pending_loans = pending_loans.filter(customer=customer)

        # Compose the message
        message = f"Dear {customer.name},\n\n"
        for i in pending_loans:
            message += f"your loan {i.loanid} is completing {i.noofmonths|add:'1'}"

        message += (
            "Please make a payment as soon as possible to avoid additional fees.\n\n"
        )
        message += "Thank you for your cooperation.\n\n"
        message += "Best regards,\nThe Loan Department"
        notify_msg(number=customer.contactno.first().phone_number, content=message)
