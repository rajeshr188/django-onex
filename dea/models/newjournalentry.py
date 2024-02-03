# from django.db import models
# from django.contrib.contenttypes.fields import GenericRelation
# straight out of chatgpt
# class Journal(models.Model):
#     date = models.DateField()
#     reference_number = models.CharField(max_length=100)
#     # Add other fields specific to the journal

#     def create_journal_entry(self, ledger_transactions, account_transactions):
#         """
#         Create a journal entry for the journal.

#         Args:
#             ledger_transactions: List of tuples (account, amount, transaction_type) representing ledger transactions.
#             account_transactions: List of tuples (account, amount, transaction_type) representing account transactions.
#         """
#         # Calculate total debit and credit amounts for ledger transactions
#         total_debit_ledger = sum(amount for _, amount, transaction_type in ledger_transactions if transaction_type == 'debit')
#         total_credit_ledger = sum(amount for _, amount, transaction_type in ledger_transactions if transaction_type == 'credit')

#         # Calculate total debit and credit amounts for account transactions
#         total_debit_account = sum(amount for _, amount, transaction_type in account_transactions if transaction_type == 'debit')
#         total_credit_account = sum(amount for _, amount, transaction_type in account_transactions if transaction_type == 'credit')

#         # Ensure the ledger transactions are balanced
#         if total_debit_ledger != total_credit_ledger:
#             raise ValueError("Ledger transactions are not balanced")

#         # Ensure the account transactions are balanced
#         if total_debit_account != total_credit_account:
#             raise ValueError("Account transactions are not balanced")

#         # Create journal entry
#         journal_entry = JournalEntry.objects.create(
#             journal=self,
#             total_debit_ledger=total_debit_ledger,
#             total_credit_ledger=total_credit_ledger,
#             total_debit_account=total_debit_account,
#             total_credit_account=total_credit_account
#         )

#         # Create ledger transactions for the journal entry
#         for account, amount, transaction_type in ledger_transactions:
#             LedgerTransaction.objects.create(
#                 journal_entry=journal_entry,
#                 account=account,
#                 amount=amount,
#                 transaction_type=transaction_type
#             )

#         # Create account transactions for the journal entry
#         for account, amount, transaction_type in account_transactions:
#             AccountTransaction.objects.create(
#                 journal_entry=journal_entry,
#                 account=account,
#                 amount=amount,
#                 transaction_type=transaction_type
#             )

#     def reverse_journal_entry(self, journal_entry_id):
#         """
#         Reverse a journal entry by creating a new set of journal entries with reversed ledger and account transactions.

#         Args:
#             journal_entry_id: ID of the journal entry to reverse.
#         """
#         # Get the original journal entry
#         original_entry = JournalEntry.objects.get(id=journal_entry_id)

#         # Create a new set of journal entries with reversed ledger transactions
#         reversed_ledger_transactions = []
#         for transaction in original_entry.ledger_transactions.all():
#             reversed_amount = -transaction.amount  # Reverse the amount
#             reversed_transaction_type = 'credit' if transaction.transaction_type == 'debit' else 'debit'
#             reversed_ledger_transactions.append((transaction.account, reversed_amount, reversed_transaction_type))

#         # Create a new set of journal entries with reversed account transactions
#         reversed_account_transactions = []
#         for transaction in original_entry.account_transactions.all():
#             reversed_amount = -transaction.amount  # Reverse the amount
#             reversed_transaction_type = 'credit' if transaction.transaction_type == 'debit' else 'debit'
#             reversed_account_transactions.append((transaction.account, reversed_amount, reversed_transaction_type))

#         self.create_journal_entry(reversed_ledger_transactions, reversed_account_transactions)


# class JournalEntry(models.Model):
#     journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='journal_entries')
#     total_debit_ledger = models.DecimalField(max_digits=15, decimal_places=2)
#     total_credit_ledger = models.DecimalField(max_digits=15, decimal_places=2)
#     total_debit_account = models.DecimalField(max_digits=15, decimal_places=2)
#     total_credit_account = models.DecimalField(max_digits=15, decimal_places=2)
