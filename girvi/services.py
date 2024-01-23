from collections import Counter

from django.db.models import Case, Count, IntegerField, Q, Sum, Value, When
from django.db.models.functions import ExtractYear

from .models import Customer, Loan, LoanItem, Release


def get_loan_counts_grouped():
    # Query to get the loan counts for each customer
    loan_counts = (
        Loan.objects.unreleased()
        .values("customer__id", "customer__name")  # Group by customer
        .annotate(loan_count=Count("id"))
        .order_by("loan_count")  # Count the number of loans
    )

    # Use Counter to group customers by loan count
    grouped_loan_counts = Counter(
        loan_count for loan_count in loan_counts.values_list("loan_count", flat=True)
    )
    # Convert the Counter to a list of tuples for easier iteration in the template
    grouped_loan_counts_list = list(grouped_loan_counts.items())

    return grouped_loan_counts_list


def get_loans_by_year():
    loans_by_year = (
        Loan.objects.annotate(
            year=ExtractYear("created"),
            has_release=Case(
                When(release__isnull=False, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
        )  # Extract year from loan start_date and check if there is a release
        .values("year")
        .annotate(
            loans_count=Count("id"),  # Count all loans
            unreleased_count=Count(
                "id", filter=Q(has_release=0)
            ),  # Count loans without a release
        )
        .order_by("year")
    )
    return loans_by_year


def get_unreleased_loans_by_year():
    data = (
        Loan.objects.unreleased()
        .annotate(year=ExtractYear("created"))  # Extract year from start_date
        .values("year")  # Group by year
        .annotate(release_count=Count("id"))  # Count the number of loans
        .order_by("year")
    )
    return data


def get_loanamount_by_itemtype():
    query = LoanItem.objects.values("itemtype").annotate(  # Group by loan type
        total_loan_amount=Sum("loanamount")
    )
    return query


def get_interest_paid():
    data = (
        Release.objects.annotate(year=ExtractYear("created"))
        .values("year")
        .annotate(total_interest=Sum("interestpaid"))
        .order_by("year")
    )
    labels = [entry["year"] for entry in data]
    interest_paid = [float(entry["total_interest"]) for entry in data]

    return data


def notify_customer(customer: Customer):
    pass


def notify_all_customers(customer: list[Customer]):
    pass
