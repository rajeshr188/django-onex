import decimal
from itertools import chain, islice, tee

from dateutil import relativedelta
from django.db import models
from django.db.models import Avg, Case, Count, FloatField, Q, Sum, When
from django.db.models.expressions import OrderBy
from django.db.models.functions import Coalesce, ExtractMonth, ExtractYear
from django.urls import reverse
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


class RelationType(models.TextChoices):
    Son = "s", "S/o"
    Daughter = "d", "D/o"
    Father = "f", "F/o"
    Child = "c", "C/o"
    Parent = "p", "P/o"
    Husband = "h", "H/o"
    Wife = "w", "W/o"
    Other = "o", "O/o"


class Customer(models.Model):
    # Fields
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        "users.CustomUser", on_delete=models.CASCADE, null=True, blank=True
    )
    name = models.CharField(max_length=255)
    firstname = models.CharField(max_length=255, blank=True)
    lastname = models.CharField(max_length=255, blank=True)
    gender = models.CharField(
        max_length=1, choices=(("M", "M"), ("F", "F"), ("N", "N")), default="M"
    )
    religion = models.CharField(
        max_length=10,
        choices=(
            ("Hindu", "Hindu"),
            ("Muslim", "Muslim"),
            ("Christian", "Christian"),
            ("Atheist", "Atheist"),
        ),
        default="Hindu",
    )
    # pic needs its own model
    pic = models.ImageField(upload_to="customer_pics/", null=True, blank=True)

    Address = models.TextField(max_length=100, blank=True)

    class CustomerType(models.TextChoices):
        Retail = "R", "Retail"
        Wholesale = "W", "Wholesale"
        Supplier = "S", "Supplier"

    customer_type = models.CharField(
        max_length=30, choices=CustomerType.choices, default=CustomerType.Retail
    )
    relatedas = models.CharField(
        max_length=5, choices=RelationType.choices, default=RelationType.Son
    )
    relatedto = models.CharField(max_length=30, blank=True)
    area = models.CharField(max_length=50, blank=True)
    active = models.BooleanField(blank=True, default=True)
    pricing_tier = models.ForeignKey(
        "product.PricingTier", on_delete=models.CASCADE, null=True, blank=True
    )

    class Meta:
        ordering = ("-created", "name", "relatedto")
        unique_together = ("name", "relatedas", "relatedto")

    def __str__(self):
        return f"""{self.name} {self.get_relatedas_display()} {self.relatedto} {self.get_customer_type_display()} \n 
                {self.address.first() } {self.contactno.first() }"""

    def get_absolute_url(self):
        return reverse("contact_customer_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("contact_customer_update", args=(self.pk,))

    # def save(self, *args, **kwargs):
    #     try:
    #         this = Customer.objects.get(id=self.id)
    #         if this.pic != self.pic:
    #             this.pic.delete(save=False)

    #     except:
    #         pass
    #     super(Customer, self).save(*args, **kwargs)

    def merge(self, dup):
        # to merge one customer into another existing one

        with transaction.atomic():
            # Transfer duplicate customer's loans to original customer
            dup.loan_set.update(customer=self)

            # Transfer duplicate customer's contacts to original customer
            dup.contactno.all().update(customer=self)

            # Delete duplicate customer
            dup.delete()

    @property
    def get_contact(self):
        return list(self.contactno.values_list("national_number", flat=True))

    @property
    def get_loans(self):
        return self.loan_set.unreleased()

    def get_total_loanamount(self):
        amount = self.loan_set.unreleased().aggregate(
            total=Coalesce(Sum("loan_amount"), 0)
        )
        return amount["total"]

    def get_total_interest_due(self):
        total_int = 0
        for i in self.get_loans:
            total_int += i.interestdue()
        return total_int

    @property
    def get_loans_count(self):
        return self.loan_set.unreleased().count()

    def get_interestdue(self):
        return self.loan_set.unreleased().aggregate(total=Sum("interest"))["total"]

    def get_weight(self):
        return 0

    @property
    def get_release_average(self):
        # Calculate the difference in months between the release and loan creation times
        release_time = Case(
            When(
                release__isnull=False,
                then=(
                    (ExtractYear("release__release_date") - ExtractYear("loan_date"))
                    * 12
                    + (
                        ExtractMonth("release__release_date")
                        - ExtractMonth("loan_date")
                    )
                ),
            ),
            When(
                release__isnull=True,
                then=(
                    (ExtractYear(timezone.now()) - ExtractYear("loan_date")) * 12
                    + (ExtractMonth(timezone.now()) - ExtractMonth("loan_date"))
                ),
            ),
            output_field=FloatField(),
        )

        # Calculate the average release time
        average_release_time = self.loan_set.released().aggregate(
            average=Avg(release_time)
        )["average"]

        return round(average_release_time) if average_release_time is not None else 0

    # sales queries
    def get_sales_invoice(self):
        return self.sales.all()

    def get_total_invoice_cash(self):
        return self.sales.aggregate(
            total=Coalesce(
                Sum("sale_balance__cash_balance", output_field=models.DecimalField()),
                decimal.Decimal(0.0),
            )
        )["total"]

    def get_total_invoice_metal(self):
        return self.sales.aggregate(
            total=Coalesce(
                Sum("sale_balance__gold_balance", output_field=models.DecimalField()),
                decimal.Decimal(0.0),
            )
        )

    def get_unpaid(self):
        return self.sales.exclude(status="Paid")

    def get_unpaid_cash(self):
        return self.get_unpaid().values("created", "id", "sale_balance")

    def get_unpaid_cash_total(self):
        return self.get_unpaid_cash().aggregate(
            total=Coalesce(Sum("sale_balance__cash_balance"), decimal.Decimal(0))
        )["total"]

    def get_unpaid_metal(self):
        return self.get_unpaid().values("created", "id", "sale_balance")

    def get_unpaid_metal_total(self):
        return self.get_unpaid_metal().aggregate(
            total=Coalesce(Sum("sale_balance__gold_balance"), decimal.Decimal(0))
        )["total"]

    def get_total_invoice_paid_cash(self):
        pass

    def get_total_invoice_paid_metal(self):
        pass

    def get_cash_receipts_total(self):
        return self.receipts.filter(type="Cash").aggregate(total=Sum("total"))["total"]

    def get_metal_receipts_total(self):
        return self.receipts.filter(type="Metal").aggregate(
            total=Coalesce(Sum("total"), decimal.Decimal(0))
        )["total"]

    def get_metal_balance(self):
        return self.get_total_invoice_metal() - self.get_metal_receipts_total()

    def get_cash_balance(self):
        return self.get_total_invoice_cash() - self.get_cash_receipts_total()

    def get_receipts(self):
        return self.receipts.all()

    def reallot_receipts(self):
        receipts = self.get_receipts()
        for i in receipts:
            i.deallot()
        for i in receipts:
            i.allot()

    def reallot_payments(self):
        payments = self.payments.all()
        for i in payments:
            i.deallot()
        for i in payments:
            i.allot()

    def previous_and_next(self, some_iterable):
        prevs, items, nexts = tee(some_iterable, 3)
        prevs = chain([None], prevs)
        nexts = chain(islice(nexts, 1, None), [None])
        return zip(prevs, items, nexts)

    def get_all_txns(self):
        sales = self.sales.all().values()
        for s in sales:
            s["type"] = "sale"

        receipts = self.receipts.all().values()
        for r in receipts:
            r["type"] = "receipt"

        purchases = self.purchases.all().values()
        for p in purchases:
            p["type"] = "purchase"

        payments = self.payments.all().values()
        for pay in payments:
            pay["type"] = "payment"

        txn_list = sorted(
            chain(sales, receipts, purchases, payments),
            key=lambda i: i["created"],
            reverse=True,
        )

        for prev, item, next in self.previous_and_next(txn_list):
            if item["type"] == "sale":
                if prev:
                    item["metal_bal"] = prev["metal_bal"] - item["balance"]
                else:
                    item["metal_bal"] = item["balance"]
            elif item["type"] == "purchase":
                if prev:
                    item["metal_bal"] = prev["metal_bal"] + item["balance"]
                else:
                    item["metal_bal"] = item["balance"]
            elif item["type"] == "receipt":
                if prev:
                    item["metal_bal"] = prev["metal_bal"] + item["total"]
                else:
                    item["metal_bal"] = item["balance"]
            elif item["type"] == "payment":
                if prev:
                    item["metal_bal"] = prev["metal_bal"] - item["total"]
                else:
                    item["metal_bal"] = item["total"]

        return txn_list


class CustomerRelationship(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="relationships"
    )
    related_customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="relatedby",
    )
    relationship = models.CharField(
        max_length=2, choices=RelationType.choices, default=RelationType.Son
    )

    class Meta:
        unique_together = ("customer", "related_customer", "relationship")

    def __str__(self):
        return f"{self.customer.name} - {self.get_relationship_display()} - {self.related_customer.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Call the "real" save() method.

        # Define the reverse relationship mapping
        reverse_relationships = {
            "s": "f",  # Son of -> Father of
            "f": "s",  # Father of -> Son of
            "d": "f",  # Daughter of -> Father of
            "c": "p",  # Child of -> Parent of
            "w": "h",  # Wife of -> Husband of
            "h": "w",  # Husband of -> Wife of
        }

        # Get the reverse relationship
        reverse_relationship = reverse_relationships.get(self.relationship)

        # Check if the reverse relationship exists
        reverse_exists = CustomerRelationship.objects.filter(
            customer=self.related_customer,
            related_customer=self.customer,
            relationship=reverse_relationship,
        ).exists()

        # If the reverse relationship doesn't exist, create it
        if not reverse_exists:
            CustomerRelationship.objects.create(
                customer=self.related_customer,
                related_customer=self.customer,
                relationship=reverse_relationship,
            )


class Address(models.Model):
    # Relationships
    Customer = models.ForeignKey(
        "contact.Customer", on_delete=models.CASCADE, related_name="address"
    )

    # Fields
    area = models.CharField(max_length=30, default="ChinaAllapuram")
    created = models.DateTimeField(auto_now_add=True, editable=False)
    doorno = models.CharField(max_length=30)
    zipcode = models.CharField(max_length=6, default="632001")
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    street = models.TextField(max_length=100)
    city = models.CharField(max_length=30, default="Vellore")

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return f"{self.doorno},{self.street},{self.area},{self.zipcode},{self.city}"

    def get_absolute_url(self):
        return reverse("Customer_Address_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("Customer_Address_update", args=(self.pk,))


class Contact(models.Model):
    # Relationships
    customer = models.ForeignKey(
        "contact.Customer", on_delete=models.CASCADE, related_name="contactno"
    )

    # Fields
    created = models.DateTimeField(auto_now_add=True, editable=False)

    class ContactType(models.TextChoices):
        Home = "H", "Home"
        Office = "O", "Office"
        Mobile = "M", "Mobile"

    contact_type = models.CharField(
        max_length=1, choices=ContactType.choices, default=ContactType.Mobile
    )
    phone_number = PhoneNumberField(unique=True)
    # is_default = models.BooleanField(default = False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return str(self.phone_number)

    def get_absolute_url(self):
        return reverse("Customer_Contact_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("Customer_Contact_update", args=(self.pk,))


class Proof(models.Model):
    # Relationships
    Customer = models.ForeignKey("contact.Customer", on_delete=models.CASCADE)

    # Fields
    class DocType(models.TextChoices):
        Aadhar = "AA", "AadharNo"
        Driving_License = "DL", "Driving License"
        Pan = "PN", "PanCard No"

    proof_type = models.CharField(
        max_length=2, choices=DocType.choices, default=DocType.Aadhar
    )
    created = models.DateTimeField(auto_now_add=True, editable=False)
    proof_no = models.CharField(max_length=30)
    doc = models.FileField(upload_to="upload/files/proofs")
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return str(self.pk)

    def get_absolute_url(self):
        return reverse("Customer_Proof_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("Customer_Proof_update", args=(self.pk,))
