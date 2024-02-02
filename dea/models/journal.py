import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.forms.models import model_to_dict
from polymorphic.models import PolymorphicModel

from .account import AccountTransaction
from .ledger import LedgerTransaction


def reverse_journal_entry(sender, instance, **kwargs):
    #     # Access model and subclass:
    if instance.pk:  # If journal is being updated
        # Retrieve the old data from the database
        old_instance = sender.objects.get(pk=instance.pk)
        print(f"Instance changed?: {instance.is_changed(old_instance)}")
        if old_instance.is_changed(instance):
            old_instance.reverse_transactions()
            instance.create_transactions()


def create_journal_entry(sender, instance, created, **kwargs):
    if created:
        print("create_journal_entry Post_save signal")
        instance.create_transactions()


class Journal(PolymorphicModel):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        "users.CustomUser", on_delete=models.CASCADE, null=True, blank=True
    )
    desc = models.TextField(blank=True, null=True)
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    posted = models.BooleanField(default=False)

    class Meta:
        get_latest_by = "created_at"

    def __str__(self):
        return f"{self.desc}"

    def get_class_name(self):
        return self.__class__.__name__

    def get_items(self):
        # By default, return None or an empty list.
        return None

    def get_journal_entry(self, desc=None):
        if self.journal_entries.exists():
            return self.journal_entries.latest()
        else:
            return JournalEntry.objects.create(
                journal=self, desc=self.__class__.__name__
            )

    def delete_journal_entry(self):
        if self.journal_entries.exists():
            self.journal_entries.delete()

    def is_changed(self, old_instance):
        # Implement logic to compare old and new instances
        # Compare all fields using dictionaries
        # print(f"old: {model_to_dict(old_instance,fields=['loanamount','customer','lid'])} new: {model_to_dict(self,fields =['loanamount','customer','lid'])}")
        return model_to_dict(
            self, fields=["loanamount", "customer", "lid"]
        ) != model_to_dict(old_instance, fields=["loanamount", "customer", "lid"])

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        models.signals.pre_save.connect(reverse_journal_entry, sender=cls)
        models.signals.post_save.connect(create_journal_entry, sender=cls)

    def get_transactions(self):
        lt = []
        at = []
        # to be defined by the subclass
        return lt, at

    def create_transactions(self):
        print("create_transactions")
        journal_entry = self.get_journal_entry()
        lt, at = self.get_transactions()
        if lt and at:
            journal_entry.transact(lt, at)

    def reverse_transactions(self):
        journal_entry = self.get_journal_entry()
        lt, at = self.get_transactions()
        if lt and at:
            journal_entry.untransact(lt, at)

    @transaction.atomic()
    def update(self):
        self.reverse_transactions()
        self.create_transactions()


class JournalEntry(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    desc = models.TextField(blank=True, null=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journal = models.ForeignKey(
        Journal, on_delete=models.CASCADE, related_name="journal_entries"
    )

    class Meta:
        get_latest_by = "id"

    def __str__(self):
        # return f"{self.journal_type}{self.desc}"
        return f"{self.desc}"

    def check_data_integrity(self, lt, at):
        # check data integrity constraints before adding transactions
        # for example, make sure the sum of debit amounts equals the sum of credit amounts
        # return True if all checks pass, False otherwise

        # Calculate total debit and credit amounts for ledger transactions
        total_debit_ledger = sum(
            amount
            for _, amount, transaction_type in ledger_transactions
            if transaction_type == "debit"
        )
        total_credit_ledger = sum(
            amount
            for _, amount, transaction_type in ledger_transactions
            if transaction_type == "credit"
        )

        # Calculate total debit and credit amounts for account transactions
        total_debit_account = sum(
            amount
            for _, amount, transaction_type in account_transactions
            if transaction_type == "debit"
        )
        total_credit_account = sum(
            amount
            for _, amount, transaction_type in account_transactions
            if transaction_type == "credit"
        )

        # Ensure the ledger transactions are balanced
        if total_debit_ledger != total_credit_ledger:
            raise ValueError("Ledger transactions are not balanced")

        # Ensure the account transactions are balanced
        if total_debit_account != total_credit_account:
            raise ValueError("Account transactions are not balanced")
        return True

    @transaction.atomic()
    def transact(self, lt, at):
        # add transactions to the journal
        # check data integrity constraints before adding transactions
        # if not self.check_data_integrity(lt,at):
        #     raise ValidationError("Data integrity violation.")

        if lt:
            for i in lt:
                # print(f"cr: {i['ledgerno']}dr:{i['ledgerno_dr']}")
                try:
                    LedgerTransaction.objects.create_txn(
                        self, i["ledgerno"], i["ledgerno_dr"], i["amount"]
                    )
                except Exception as e:
                    print(f"error: {e}")

        if at:
            for i in at:
                try:
                    AccountTransaction.objects.create_txn(
                        self,
                        i["ledgerno"],
                        i["xacttypecode"],
                        i["xacttypecode_ext"],
                        i["account"],
                        i["amount"],
                    )
                except Exception as e:
                    print(f"error: {e}")
        print("transact done")

    @transaction.atomic()
    def untransact(self, lt, at):
        for i in lt:
            # print(f"txn:{i}")
            # print(f"cr: {i['ledgerno']} dr:{i['ledgerno_dr']}")
            LedgerTransaction.objects.create_txn(
                self, i["ledgerno_dr"], i["ledgerno"], i["amount"]
            )

        for i in at:
            xacttypecode = ""
            xacttypecode_ext = ""
            if i["xacttypecode"] == "Cr":
                xacttypecode = "Dr"
                xacttypecode_ext = "AC"
            else:
                xacttypecode = "Cr"
                xacttypecode_ext = "AD"
            AccountTransaction.objects.create_txn(
                self,
                i["ledgerno"],
                xacttypecode,
                xacttypecode_ext,
                i["account"],
                i["amount"],
            )
