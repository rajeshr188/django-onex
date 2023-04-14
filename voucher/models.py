from django.db import models

# Create your models here.
from django.db import models
from django.core.exceptions import ValidationError

class Voucher(models.Model):
    # fields
    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)
    # other fields such as voucher number, voucher date, etc.

    class Meta:
        abstract = True
    # methods
    def save(self, *args, **kwargs):
        if not self.pk:
            # create the journal for this voucher
            journal = Journal.objects.create(voucher=self, type='ledger')
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

    def create_journals(self):
        ledger_journal = Journal.objects.create(voucher=self, type='ledger')
        account_journal = Journal.objects.create(voucher=self, type='account')
        return ledger_journal, account_journal

    def get_journals(self):
        ledger_journal = Journal.objects.get(voucher=self, type='ledger')
        account_journal = Journal.objects.get(voucher=self, type='account')
        return ledger_journal, account_journal

    def delete_journals(self):
        self.journals.all().delete()

    def get_transactions(self):
        ledger_transactions = {}
        account_transactions = {}
        return ledger_transactions, account_transactions

    @transaction.atomic()
    def create_transactions(self):
        # create account transactions
        account_transactions = []
        # ... create account transactions based on the voucher and voucher items
        # create ledger transactions
        ledger_transactions = []
        # ... create ledger transactions based on the voucher and voucher items
        # save transactions to the journal
        self.journal.add_transactions(account_transactions + ledger_transactions)

    @transaction.atomic()
    def reverse_transactions(self):
        # reverse account transactions
        account_transactions = []
        # ... reverse account transactions based on the voucher and voucher items
        # reverse ledger transactions
        ledger_transactions = []
        # ... reverse ledger transactions based on the voucher and voucher items
        # save reversed transactions to the journal
        self.journal.add_transactions(account_transactions + ledger_transactions)


class VoucherItem(models.Model):
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f'{self.item} - {self.quantity}'
    
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
            previous_balance=previous_transaction.balance if previous_transaction else 0,
            new_balance=new_balance,
            timestamp=timezone.now()
        )
        stock_transaction.save()
        
        # update the voucher's balance
        self.voucher.update()
        
        super().save(*args, **kwargs)
    
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
            previous_balance=previous_transaction.balance if previous_transaction else 0,
            new_balance=new_balance,
            timestamp=timezone.now()
        )
        stock_transaction.save()
        
        # update the voucher's balance
        self.voucher.update()
        
        super().delete(*args, **kwargs)
    
    def get_previous_stock_transaction(self):
        """
        Get the previous stock transaction for this item
        """
        return StockTransaction.objects.filter(item=self.item, voucher=self.voucher).order_by('-timestamp').first()
    
    def get_updated_balance(self):
        """
        Calculate the updated balance for this item
        """
        previous_transaction = self.get_previous_stock_transaction()
        previous_balance = previous_transaction.balance if previous_transaction else 0
        return previous_balance + Decimal(self.quantity) * Decimal(self.rate)

# --------------------------------composition--------------------------------
# from django.db import models

# class Voucher(models.Model):
#     # common fields for all vouchers
    
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     voucher_type = models.CharField(max_length=255)
    
#     def save(self, *args, **kwargs):
#         # calculate voucher balance
#         voucher_items = self.voucher_items.all()
#         voucher_balance = sum([item.balance for item in voucher_items])
#         self.balance = voucher_balance
        
#         super().save(*args, **kwargs)
    
# class SalesVoucher(models.Model):
#     voucher = models.OneToOneField(Voucher, on_delete=models.CASCADE, related_name='sales_voucher')
    
#     # fields specific to sales voucher
#     customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
#     invoice_number = models.CharField(max_length=255)
    
#     def create_journal(self):
#         # create ledger and account journals for sales voucher
#         # ...
    
#     def create_transactions(self):
#         # create ledger and account transactions for sales voucher
#         # ...
    
#     def reverse_transactions(self):
#         # reverse ledger and account transactions for sales voucher
#         # ...
    
# class PurchaseVoucher(models.Model):
#     voucher = models.OneToOneField(Voucher, on_delete=models.CASCADE, related_name='purchase_voucher')
    
#     # fields specific to purchase voucher
#     supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
#     purchase_order_number = models.CharField(max_length=255)
    
#     def create_journal(self):
#         # create ledger and account journals for purchase voucher
#         # ...
    
#     def create_transactions(self):
#         # create ledger and account transactions for purchase voucher
#         # ...
    
#     def reverse_transactions(self):
#         # reverse ledger and account transactions for purchase voucher
#         # ...
    
# other voucher types modeled similarly...
