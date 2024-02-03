from django.core.exceptions import ValidationError
# Create your models here.
from django.db import models


# ---------------------------------- Voucher(Generic ForeignKey) ----------------------------------
class Voucher(models.Model):
    # fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField()

    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_ratecut = models.BooleanField(default=False)
    is_gst = models.BooleanField(default=False)

    gold_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    silver_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cash_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # multicurrency using django-money with postgres array field
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # other fields such as voucher number, voucher date, etc.

    class Meta:
        abstract = True

    # methods
    def save(self, *args, **kwargs):
        if not self.pk:
            # create the journal for this voucher
            journal = Journal.objects.create(voucher=self, type="ledger")
            self.journal = journal

        # calculate voucher balance
        voucher_items = self.voucher_items.all()
        voucher_balance = sum([item.balance for item in voucher_items])
        self.balance = voucher_balance
        super().save(*args, **kwargs)

    def update(self, *args, **kwargs):
        # reverse existing transactions before updating the voucher
        self.reverse_transactions()
        super().update(*args, **kwargs)
        # create new transactions based on the updated voucher
        self.create_transactions()

    @property
    def balance(self):
        """
        Calculates the voucher balance based on its associated voucher items in a view
        """
        try:
            return self.voucher_balance.balance
        except VoucherBalance.DoesNotExist:
            return Decimal(0)

    def update_status(self):
        """
        Updates the voucher status based on its balance
        """
        if self.balance == 0:
            self.status = "paid"
        elif self.balance > 0:
            self.status = "due"
        elif self.balance < 0:
            self.status = "overpaid"
        self.save()

    def get_journals(self):
        """
        Returns a queryset of all journals associated with this voucher
        """
        # raise NotImplementedError("get_journals() must be implemented by descendant models")
        ledger_journal = Journal.objects.get(content_object=self, journal_type="ledger")
        account_journal = Journal.objects.get(
            content_object=self, journal_type="account"
        )
        return ledger_journal, account_journal

    def create_journals(self):
        """
        Creates the journal entries for this voucher and saves them to the database
        """
        # raise NotImplementedError("create_journals() must be implemented by descendant models")
        ledger_journal = Journal.objects.create(
            content_object=self, journal_type="ledger"
        )
        account_journal = Journal.objects.create(
            content_object=self, journal_type="account"
        )
        return ledger_journal, account_journal

    def get_transactions(self):
        """
        Returns a queryset of all transactions associated with this voucher
        ledger_transactions = {}
        account_transactions = {}
        return ledger_transactions, account_transactions
        """
        raise NotImplementedError(
            "get_transactions() must be implemented by descendant models"
        )

    def create_transactions(self):
        """
        Creates the transactions for this voucher and saves them to the database
        """
        raise NotImplementedError(
            "create_transactions() must be implemented by descendant models"
        )

    def reverse_transactions(self):
        """
        Reverses the transactions for this voucher and saves them to the database
        """
        raise NotImplementedError(
            "reverse_transactions() must be implemented by descendant models"
        )

    def delete_journals(self):
        """
        Deletes all journal entries associated with this voucher
        """
        # raise NotImplementedError("delete_journals() must be implemented by descendant models")
        self.journals.all().delete()

        # @transaction.atomic()
        # def create_transactions(self):
        #     # create account transactions
        #     account_transactions = []
        #     # ... create account transactions based on the voucher and voucher items
        #     # create ledger transactions
        #     ledger_transactions = []
        #     # ... create ledger transactions based on the voucher and voucher items
        #     # save transactions to the journal
        #     self.journal.add_transactions(account_transactions + ledger_transactions)

        # @transaction.atomic()
        # def reverse_transactions(self):
        # reverse account transactions
        account_transactions = []
        # ... reverse account transactions based on the voucher and voucher items
        # reverse ledger transactions
        ledger_transactions = []
        # ... reverse ledger transactions based on the voucher and voucher items
        # save reversed transactions to the journal
        self.journal.add_transactions(account_transactions + ledger_transactions)


class VoucherBalance(models.Model):
    voucher = models.OneToOneField(Voucher, on_delete=models.CASCADE, primary_key=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = "voucher_balance"


class VoucherItem(models.Model):
    # foreign keys
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE, related_name="items")
    # fields
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    less_weight = models.DecimalField(max_digits=10, decimal_places=2)
    touch = models.DecimalField(max_digits=10, decimal_places=2)
    nett_weight = models.DecimalField(max_digits=10, decimal_places=2)
    making_charge = models.DecimalField(max_digits=10, decimal_places=2)
    hallmark_charge = models.DecimalField(max_digits=10, decimal_places=2)
    metal_balance = models.DecimalField(max_digits=10, decimal_places=2)
    cash_balance = models.DecimalField(max_digits=10, decimal_places=2)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """
        Create a new stock transaction and update the voucher's balance
        """
        previous_transaction = self.get_previous_stock_transaction()
        new_balance = self.get_updated_balance()

        # create a new stock transaction
        stock_journal = Journal.objects.get(type=JournalType.STOCK)
        stock_transaction = StockTransaction(
            item=self.item,
            journal=stock_journal,
            voucher=self.voucher,
            quantity=self.quantity,
            rate=self.rate,
            previous_balance=previous_transaction.balance
            if previous_transaction
            else 0,
            new_balance=new_balance,
            timestamp=timezone.now(),
        )
        stock_transaction.save()

        # update the voucher's balance
        self.voucher.update()

        super().save(*args, **kwargs)

    def save(self, *args, **kwargs):
        """
        Overrides the save method to update the associated voucher's balance
        """
        self.metal_balance = self.weight * self.touch
        if self.voucher.ratecut:
            self.cash_balance = self.metal_balance * self.voucher.rate
        else:
            self.cash_balance = 0
        super().save(*args, **kwargs)
        self.voucher.update_balance()

    def delete(self, *args, **kwargs):
        """
        Reverse the existing stock transaction and update the voucher's balance
        """
        previous_transaction = self.get_previous_stock_transaction()
        new_balance = self.get_updated_balance()

        # reverse the existing stock transaction
        stock_journal = Journal.objects.get(type=JournalType.STOCK)
        stock_transaction = StockTransaction(
            item=self.item,
            journal=stock_journal,
            voucher=self.voucher,
            quantity=self.quantity * -1,
            rate=self.rate,
            previous_balance=previous_transaction.balance
            if previous_transaction
            else 0,
            new_balance=new_balance,
            timestamp=timezone.now(),
        )
        stock_transaction.save()

        # update the voucher's balance
        self.voucher.update()

        super().delete(*args, **kwargs)

    def get_previous_stock_transaction(self):
        """
        Get the previous stock transaction for this item
        """
        return (
            StockTransaction.objects.filter(item=self.item, voucher=self.voucher)
            .order_by("-timestamp")
            .first()
        )

    def get_updated_balance(self):
        """
        Calculate the updated balance for this item
        """
        previous_transaction = self.get_previous_stock_transaction()
        previous_balance = previous_transaction.balance if previous_transaction else 0
        return previous_balance + Decimal(self.quantity) * Decimal(self.rate)

    def create_journal(self):
        """
        Creates a journal entry for this voucher item
        """
        # raise NotImplementedError("create_journal() must be implemented by descendant models")
        stock_journal = Journal.objects.create(
            content_object=self,
            journal_type=JournalTypes.SJ,
            desc=f"for {self.invoice.pk}",
        )
        return stock_journal

    def get_journal(self):
        """
        Returns the journal entry for this voucher item
        """
        # raise NotImplementedError("get_journal() must be implemented by descendant models")
        stock_journal = self.journal
        if stock_journal.exists():
            return stock_journal.first()
        return self.create_journal()

    def post(self):
        """
        Posts the journal entry for this voucher item
        """
        raise NotImplementedError("post() must be implemented by descendant models")

    def reverse(self):
        """
        Reverses the journal entry for this voucher item
        """
        raise NotImplementedError("reverse() must be implemented by descendant models")
