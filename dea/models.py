from django.db import models,transaction,connection
from django.core.validators import MinValueValidator
from django.contrib.postgres.fields import ArrayField
from django.urls import reverse
from django.utils import timezone
from moneyed.classes import LSL
from mptt.models import MPTTModel,TreeForeignKey
from django.db.models import Sum
from contact.models import Customer
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from djmoney.models.fields import MoneyField
from moneyed import Money
from .utils.currency import Balance
from psycopg2.extras import register_composite
from psycopg2.extensions import register_adapter, adapt, AsIs
from . import managers

MoneyValue = register_composite(
    'money_value',
    connection.cursor().cursor,
    globally=True
).type

def moneyvalue_adapter(value):
    return AsIs("(%s,%s)::money_value" % (
        adapt(value.amount),
        adapt(value.currency.code)))

register_adapter(Money, moneyvalue_adapter)

class MoneyValueField(models.Field):
    description = "wrapper for money_value composite type in postgres"
    
    def from_db_value(self,value,expression,connection):
        if value is None:
            return value
        return Money(value.amount,value.currency)
        
    def to_python(self,value):
        if isinstance(value,Money):
            return value
        if value is None:
            return value
        return Money(value.amount,value.currency.code)

    def get_prep_value(self, value):
        # in admin input box we enter 10 USD,20 INR,30 AUD

        if isinstance(value,Money):
            return value
        else:
            amount,currency = value.split()
            return Money(amount,currency)
        
    def db_type(self,connection):
        return 'money_value'

# Create your models here.

# cr credit,dr debit
class TransactionType_DE(models.Model):
    XactTypeCode = models.CharField(max_length=2,primary_key=True)
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name

# sundry_debtor[dr],sundry_creditor[cr],let desc be unique
class AccountType_Ext(models.Model):
    XactTypeCode = models.ForeignKey(TransactionType_DE ,
                        on_delete=models.CASCADE)
    description = models.CharField(max_length=100,unique = True)

    def __str__(self):
        return self.description

# person or organisation
class EntityType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# rameshbi[sundry debtor],ramlalji,narsa,mjk[sundry creditor]
# add accountno
class Account(models.Model):
    entity = models.ForeignKey(EntityType,
                        null = True,
                        on_delete = models.SET_NULL,
                        )
    AccountType_Ext = models.ForeignKey(AccountType_Ext,
                        on_delete = models.CASCADE,
                        )

    contact = models.OneToOneField(Customer,
                        on_delete = models.CASCADE,
                        related_name='account'
                        )
    objects = managers.AccountManager()
    class Meta:
        ordering = ('id',)

    def __str__(self):
        return f"{self.id}"
        
    def get_absolute_url(self):
        return reverse("dea_account_detail", kwargs={"pk": self.pk})
    
    def set_opening_bal(self,amount):
        # amount is a MoneyField
        # ensure there aint no txns before setting op bal if present then audit and adjust
        return AccountStatement.objects.create(self,ClosingBalance = Balance(amount))

    def adjust(self,amount,xacttypecode):
        pass

    def audit(self): 
        ls = self.latest_stmt() 
        if ls is None:
            since = None
        else:
            since = ls.created
        credit_t = self.total_credit(since = since).monies()
        debit_t = self.total_debit(since = since).monies()
        return AccountStatement.objects.create(AccountNo =self,
                             ClosingBalance = self.current_balance().monies(),
                             TotalCredit = credit_t,
                             TotalDebit = debit_t)
    def latest_stmt(self):
        try:
            return self.accountstatements.latest()
        except AccountStatement.DoesNotExist:
            return None

    def txns(self,since = None):    
        if since is not None:
            return self.accounttransactions.filter(
                created__gte = since
            )
        else:
            return self.accounttransactions.all()

    def total_credit(self,since = None):
        txns = self.txns(since = since)
        return Balance(
            [Money(r["total"], r["amount_currency"])
             for r in txns.filter(XactTypeCode__XactTypeCode='Dr')
             .values("amount_currency")
             .annotate(total=Sum("amount"))]
        )
             
    def total_debit(self,since = None):
        txns = self.txns(since = since)
        return Balance(
            [Money(r["total"], r["amount_currency"])
             for r in txns.filter(XactTypeCode__XactTypeCode='Cr')
             .values("amount_currency")
             .annotate(total=Sum("amount"))]
        )
        
    def current_balance(self):
        ls = self.latest_stmt()
        if ls is None:
            cb = Balance()
            ac_txn = self.txns()
        else:
            cb = ls.get_cb()
            ac_txn = self.txns(since = ls.created)

        credit = ac_txn\
                    .filter(XactTypeCode_ext__in = ['LT','LR','IR','CPU','CRPU','RCT','AC'])\
                        .values("amount_currency")\
                            .annotate(total = Sum('amount'))
        debit = ac_txn\
                    .filter(XactTypeCode_ext__in=['LG', 'LP', 'IP','PYT','CRSL','AD'])\
                        .values("amount_currency")\
                            .annotate(total=Sum('amount'))
        credit_bal = Balance(
                        [Money(r["total"], r["amount_currency"]) for r in credit]) 
                        
        debit_bal =  Balance(
                        [Money(r["total"], r["amount_currency"]) for r in debit])
        bal = (cb +(credit_bal - debit_bal))

        return bal
        
# account statement for ext account
class AccountStatement(models.Model):
    AccountNo = models.ForeignKey(Account,
                        on_delete = models.CASCADE,
                        related_name='accountstatements')
    created = models.DateTimeField(
        # unique = True, 
        auto_now_add = True)
    ClosingBalance = ArrayField(MoneyValueField(null = True,blank = True))
    TotalCredit = ArrayField(MoneyValueField(null = True,blank = True))
    TotalDebit = ArrayField(MoneyValueField(null=True, blank=True))
    
    class Meta:
        get_latest_by = 'created'

    def __str__(self):
        return f"{self.id} | {self.AccountNo} = {self.ClosingBalance}({self.TotalDebit} - {self.TotalCredit})"

    def get_cb(self):
        return Balance(self.ClosingBalance)

# sales,purchase,receipt,payment,loan,release
class TransactionType_Ext(models.Model):
    XactTypeCode_ext = models.CharField(max_length=4,primary_key= True)
    description = models.CharField(max_length=100)

    def __str__(self):
        return self.XactTypeCode_ext

# ledger account type  for COA ,asset,liability,revenue,expense,gain,loss
class AccountType(models.Model):
    AccountType = models.CharField(max_length=50)
    description = models.CharField(max_length=100)

    def __str__(self):
        return self.AccountType

# ledger is chart of accounts
# add ledgerno
class Ledger(MPTTModel):
    AccountType = models.ForeignKey(AccountType,
                    on_delete = models.CASCADE)
    name = models.CharField(max_length=100)
    parent = TreeForeignKey('self',
                            null = True,
                            blank = True,
                            on_delete = models.CASCADE,
                            related_name = 'children')
    objects = managers.LedgerManager()
    
    class MPTTMeta:
        order_insertion_by = ['name']
        constraints = [
        models.UniqueConstraint(fields=['name', 'parent'], name='unique ledgername-parent')
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("dea_ledger_detail", kwargs={"pk": self.pk})
    
    def get_latest_stmt(self):
        try:
            return self.ledgerstatements.latest()
        except LedgerStatement.DoesNotExist:
            return None

    def get_closing_balance(self):
        ls = self.get_latest_stmt()
        if ls is None:
            return Balance()
        else:
            return Balance(ls.ClosingBalance)

    def set_opening_bal(self,amount):
        # ensure there aint no txns before setting op bal if present then audit and adjust
        return LedgerStatement.objects.create(self,amount)

    def adjust(self,xacttypcode,amount):
        pass
    
    def ctxns(self,since = None):
        if since is not None:
            return self.credit_txns.filter(created__gte=since)
        else:
            return self.credit_txns.all()
      
    def dtxns(self,since = None):
        if since is not None:
            return self.debit_txns.filter(created__gte=since)
        else:
            return self.debit_txns.all()
   
    def audit(self):
        # this statement will serve as opening balance for this acc
        return LedgerStatement.objects.create(ledgerno=self,
                                              ClosingBalance=self.current_balance().monies())
    
    def current_balance(self):

        # decendants = self.get_descendants(include_self = True)

        # bal = [Balance([Money(r["total"], r["amount_currency"]) 
        #                 for r in acc.debit_txns.values("amount_currency").annotate(total = Sum("amount"))])
        #         - 
        #        Balance([Money(r["total"], r["amount_currency"])
        #                 for r in acc.credit_txns.values("amount_currency").annotate(total = Sum("amount"))])
        #         for acc in decendants
        #         ]
        ls = self.get_latest_stmt()
        if ls is None:
            cb = Balance()
            since = None
        else:
            cb = ls.get_cb()
            since = ls.created
        c_bal = Balance(
            [Money(r['total'],r["amount_currency"]) for r in self.ctxns(since).values('amount_currency').annotate(total = Sum('amount'))])\
                if self.ctxns(since = since) else Balance()
        d_bal = Balance( 
            [Money(r['total'],r["amount_currency"]) for r in self.dtxns(since).values('amount_currency').annotate(total = Sum('amount'))])\
                if self.dtxns(since = since) else Balance()

        bal = cb + d_bal - c_bal
        
        return bal

class Journal(models.Model):

    created = models.DateTimeField(auto_now_add =True)
    
    base_type = managers.JournalTypes.BJ
    type = models.CharField(max_length = 50,choices = managers.JournalTypes.choices,
                        default = base_type)
    desc = models.TextField(blank = True,null = True)
    # Below the mandatory fields for generic relation
    content_type = models.ForeignKey(ContentType,
                        blank = True,null = True,
                        on_delete=models.SET_NULL)
    object_id = models.PositiveIntegerField(blank = True,null = True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return self.desc

    def get_url_string(self):
        if self.content_type:
            return f"{self.content_type.app_label}_{self.content_type.model}_detail"
    
    def save(self,*args,**kwargs):
        if not self.id:
            self.type = self.base_type
        return super().save(*args,**kwargs)

    def transact(self):
        raise NotImplementedError

class LedgerTransactionManager(models.Manager):
    def create_txn(self,journal,ledgerno_dr,ledgerno,amount):
        dr = Ledger.objects.get(name = ledgerno_dr)
        cr = Ledger.objects.get(name = ledgerno)
        txn = self.create(journal = journal,ledgerno = cr,ledgerno_dr=dr,amount = amount)
        return txn

class LedgerTransaction(models.Model):
    journal = models.ForeignKey(Journal,on_delete = models.CASCADE,related_name='ltxns')
    ledgerno = models.ForeignKey(Ledger,on_delete =models.CASCADE ,
                    related_name='credit_txns')
    created = models.DateTimeField(auto_now_add = True,
                    # unique = True
                    )
    ledgerno_dr = models.ForeignKey(Ledger ,on_delete =models.CASCADE, 
                    related_name= 'debit_txns')
    # amount = models.DecimalField(max_digits=13, decimal_places=3)
    amount = MoneyField(max_digits=13,decimal_places=3,default_currency='INR',
                    validators =[ MinValueValidator(limit_value= 0.0)])
    objects = LedgerTransactionManager()

    def __str__(self):
        return self.ledgerno.name
 
class LedgerStatement(models.Model):
    ledgerno = models.ForeignKey(Ledger,on_delete = models.CASCADE,
                        related_name='ledgerstatements')
    created = models.DateTimeField(
        # unique = True,
        auto_now_add=True)
    # ClosingBalance = models.DecimalField(max_digits=13, decimal_places=3)
    ClosingBalance = ArrayField(MoneyValueField(null=True, blank=True))
    
    class Meta:
        get_latest_by = 'created'
        ordering = ['-created']

    def __str__(self):
        return f"{self.created.date()} - {self.ledgerno} - {self.ClosingBalance}"

    def get_cb(self):
        return Balance(self.ClosingBalance)

class AccountTransactionManager(models.Manager):
    def create_txn(self,journal, ledgerno, xacttypecode, xacttypecode_ext, account, amount):
        l = Ledger.objects.get(name=ledgerno)
        xc = TransactionType_DE.objects.get(XactTypeCode = xacttypecode)
        xc_ext = TransactionType_Ext.objects.get(XactTypeCode_ext = xacttypecode_ext)
        txn = self.create(journal = journal,ledgerno = l,XactTypeCode = xc,
                XactTypeCode_ext = xc_ext,Account = account,amount = amount)
        return txn

class AccountTransaction(models.Model):
    journal = models.ForeignKey(Journal,on_delete = models.CASCADE,related_name='atxns')
    ledgerno = models.ForeignKey(Ledger,on_delete = models.CASCADE)
    created = models.DateTimeField(auto_now_add= True,
                        # unique = True
                        )
    XactTypeCode = models.ForeignKey(TransactionType_DE,
                    on_delete = models.CASCADE)
    XactTypeCode_ext = models.ForeignKey(TransactionType_Ext,
                        on_delete=models.CASCADE)
    Account = models.ForeignKey(Account,on_delete=models.CASCADE,
                            related_name='accounttransactions')
    amount = MoneyField(max_digits=13,decimal_places=3,default_currency='INR',
                        validators=[MinValueValidator(limit_value=0.0)])
    objects = AccountTransactionManager()
    def __str__(self):
        return f"{self.XactTypeCode_ext}"

# proxy models for all types of journals
# all journals to be seperated into another file figure out how

class LoanGivenJournal(Journal):
    base_type = managers.JournalTypes.LG
    objects = managers.LoanGivenJournalManager()
    class Meta:
        proxy = True
    
    @transaction.atomic()
    def transact(self):

        account = self.content_object.customer.account
        amount = Money(self.content_object.loanamount,"INR")
        asset_loan = Ledger.objects.get(name="Loans & Advances")
        cash_ledger_Acc = Ledger.objects.get(name="Cash")
        cr = TransactionType_DE.objects.get(XactTypeCode='Cr')
        lg = TransactionType_Ext.objects.get(
            XactTypeCode_ext='LG'
        )
        LedgerTransaction.objects.create(
            journal=self,
            ledgerno=cash_ledger_Acc,
            ledgerno_dr=asset_loan, amount=amount
        )
        AccountTransaction.objects.create(
            journal=self,
            ledgerno=asset_loan, XactTypeCode=cr,
            XactTypeCode_ext=lg, Account=account, amount=amount
        )

class LoanTakenJournal(Journal):
    base_type = managers.JournalTypes.LT
    objects = managers.LoanTakenJournalManager()

    class Meta:
        proxy = True

    @transaction.atomic()
    def transact(self):
        account = self.content_object.customer.account
        amount = Money(self.content_object.loanamount,"INR")
        liability_loan = Ledger.objects.get(name = 'Loans')
        cash_ledger_Acc = Ledger.objects.get(name = 'Cash')
        lt = TransactionType_Ext.objects.get(XactTypeCode_ext = 'LT')
        dr = TransactionType_DE.objects.get(XactTypeCode = 'Dr')

        AccountTransaction.objects.create(
            journal=self,
            ledgerno=liability_loan,
            XactTypeCode=dr,
            XactTypeCode_ext=lt,
            Account=account,
            amount=amount
        )
        LedgerTransaction.objects.create(
            journal=self,
            ledgerno=liability_loan,
            ledgerno_dr=cash_ledger_Acc,
            amount=amount)

class InterestPaidJournal(Journal):
    base_type = managers.JournalTypes.IP
    objects = managers.InterestPaidJournalManager()
    
    class Meta:
        proxy = True

    @transaction.atomic()
    def transact(self):
        account = self.content_object.customer.account
        amount = self.content_object.interest
        ip = TransactionType_Ext.objects.get(XactTypeCode_ext='IP')
        int_paid = Ledger.objects.get(name='Interest Paid')
        int_payable = Ledger.objects.get(name='Interest Payable')
        cash_ledger_Acc = Ledger.objects.get(name="Cash")
        cr = TransactionType_DE.objects.get(XactTypeCode='Cr')

        LedgerTransaction.objects.create(
            journal=self,
            ledgerno = cash_ledger_Acc,
            ledgerno_dr = int_payable,amount = amount
            )
        LedgerTransaction.objects.create(
            journal = self,
            ledgerno = int_payable,
            ledgerno_dr = int_paid,amount = amount
        )
        AccountTransaction.objects.create(
            journal=self,
            ledgerno = int_payable,XactTypeCode = cr,
            XactTypeCode_ext = ip,Account = account,amount = amount
        )

class InterestReceivedJournal(Journal):
    base_type = managers.JournalTypes.IR
    objects = managers.InterestReceivedJournalManager()

    class Meta:
        proxy = True

    def transact(self):
        account= self.content_object.customer.account
        interest = self.content_object.interest_due()
        int_received = Ledger.objects.get(name="Interest Received")
        cash_ledger_Acc = Ledger.objects.get(name="Cash")
        int_receivable = Ledger.objects.get(name='Interest Receivable')

        ir = TransactionType_Ext.objects.get(XactTypeCode_ext='IR')
        dr = TransactionType_DE.objects.get(XactTypeCode='Dr')

        LedgerTransaction.objects.create(
            journal=self,
            ledgerno=int_received,
            ledgerno_dr=int_receivable, amount=interest
        )
        LedgerTransaction.objects.create(
            journal=self,
            ledgerno=int_receivable,
            ledgerno_dr=cash_ledger_Acc, amount=interest
        )
        AccountTransaction.objects.create(
            journal=self,
            ledgerno=int_received,
            XactTypeCode=dr, XactTypeCode_ext=ir,
            Account=account, amount=interest
        )

class LoanReleaseJournal(Journal):
    base_type = managers.JournalTypes.LR
    objects = managers.LoanReleaseJournalManager()

    class Meta:
        proxy = True

    @transaction.atomic()
    def transact(self):
        account = self.content_object.customer.account
        amount = Money(self.content_object.get_total(),"INR")
        cash_ledger_Acc = Ledger.objects.get(name="Cash")
        lr = TransactionType_Ext.objects.get(XactTypeCode_ext='LR')
        dr = TransactionType_DE.objects.get(XactTypeCode='Dr')

        asset_loan = Ledger.objects.get(name="Loans & Advances")
        LedgerTransaction.objects.create(
            journal=self,
            ledgerno=asset_loan, ledgerno_dr=cash_ledger_Acc, amount=amount
        )
        AccountTransaction.objects.create(
            journal=self,
            ledgerno=asset_loan, XactTypeCode=dr,
            XactTypeCode_ext=lr, Account=account, amount=amount
        )

class LoanPaidJournal(Journal):
    
    base_type = managers.JournalTypes.LP
    objects = managers.LoanRepayJournalManager()

    class Meta:
        proxy = True

    @transaction.atomic()
    def transact(self):
        account = self.content_object.customer.account
        amount = self.content_object.get_total()
        lp = TransactionType_Ext.objects.get(XactTypeCode_ext='LP')
        cr = TransactionType_DE.objects.get(XactTypeCode='Cr')
        cash_ledger_acc = Ledger.objects.get(name="Cash")

        if account.AccountType_Ext.description == "Creditor":
            liability_loan = Ledger.objects.get(name="Loans")

            AccountTransaction.objects.create(
                journal=self,
                ledgerno=liability_loan, XactTypeCode=cr,
                XactTypeCode_ext=lp, Account=account, amount=amount)

            LedgerTransaction.objects.create(
                journal=self,
                ledgerno=cash_ledger_acc,
                ledgerno_dr=liability_loan, amount=amount)

class SalesJournal(Journal):
    base_type = managers.JournalTypes.SJ
    objects = managers.SalesJournalManager()

    class Meta:
        proxy = True

    def transact(self,revert = False):
       
        account = self.content_object.customer.account
        amount = self.content_object.balance
        tax = self.content_object.get_gst()
        balance_type = self.content_object.balancetype
        inv = "GST INV" if self.content_object.is_gst else "Non-GST INV"
        cogs = "GST COGS" if self.content_object.is_gst else "Non-GST COGS"
                
        if balance_type == 'Cash':
            money = Money(amount, 'INR')
        elif balance_type == 'Gold':
            money = Money(amount, 'USD')
        else:
            money = Money(amount, 'AUD')

        if not revert:
            LedgerTransaction.objects.create_txn(
                journal=self,
                ledgerno = 'Sales',ledgerno_dr = 'Sundry Debtors',amount = money)
            LedgerTransaction.objects.create_txn(
                    journal=self,
                    ledgerno = inv,ledgerno_dr = cogs,amount = money
                )
            LedgerTransaction.objects.create_txn(
                journal = self,
                ledgerno = "IGST", ledgerno_dr = "Sundry Debtors",amount = Money(tax,'INR'))
            AccountTransaction.objects.create_txn(
                journal = self,
                ledgerno = "Sales",xacttypecode = "Cr",
                xacttypecode_ext = "CRSL",account = account,amount = amount
            )
        else:
            LedgerTransaction.objects.create_txn(
                journal=self,
                ledgerno="Sundry Debtors", ledgerno_dr="Sales", amount=money)
            LedgerTransaction.objects.create(
                journal=self,
                ledgerno=cogs, ledgerno_dr="Inventory", amount=money
            )
            LedgerTransaction.objects.create_txn(
                journal=self,
                ledgerno="Sundry Debtors", ledgerno_dr="IGST", amount=Money(tax, 'INR'))
            AccountTransaction.objects.create_txn(
                journal=self,
                ledgerno="Sales", xacttypecode="Dr",
                xacttypecode_ext="AC", account=account, amount=amount
            )

class SaleReturnJournal(Journal):
    base_type = managers.JournalTypes.SR
    class Meta:
        proxy = True

class ReceiptJournal(Journal):
    base_type = managers.JournalTypes.RC
    objects = managers.ReceiptJournalManager()

    class Meta:
        proxy = True

    def transact(self,revert = False):
        account = self.content_object.customer.account
        amount = self.content_object.total
        balance_type = self.content_object.type
        cash_ac = Ledger.objects.get(name ='Cash In Drawer')
        acc_recv = Ledger.objects.get(name = 'Accounts Receivables')
        cr = TransactionType_DE.objects.get(XactTypeCode ='Cr')
        dr = TransactionType_DE.objects.get(XactTypeCode='Dr')
        sre = TransactionType_Ext.objects.get(XactTypeCode_ext = 'RCT')
        ca = TransactionType_Ext.objects.get(XactTypeCode_ext='AC')
        if balance_type =='Cash':
            money = Money(amount,'INR')
        elif balance_type =='Gold':
            money = Money(amount,'USD')
        else:
            money = Money(amount,'AUD')
        
        if not revert:
            LedgerTransaction.objects.create(
                journal = self,
                ledgerno = acc_recv,ledgerno_dr = cash_ac,amount = money
            )
            AccountTransaction.objects.create(
                journal = self,
                ledgerno = acc_recv,XactTypeCode =cr,
                XactTypeCode_ext =sre, Account = account,amount = money
            )
        else:
            LedgerTransaction.objects.create(
                journal = self,
                ledgerno=cash_ac, ledgerno_dr=acc_recv, amount=money
            )
            AccountTransaction.objects.create(
                journal = self,
                ledgerno = acc_recv,XactTypeCode =dr,
                XactTypeCode_ext =ca, Account = account,amount = money
            )

class PurchaseJournal(Journal):
    base_type = managers.JournalTypes.PJ
    purchase = managers.PurchaseJournalManager()

    class Meta:
        proxy =True

    @transaction.atomic()
    def transact(self,revert = False):
        account = self.content_object.supplier.account
        amount = self.content_object.balance
        tax =  self.content_object.get_gst()
        balance_type = self.content_object.balancetype
        inv = "GST INV" if self.content_object.is_gst else "Non-GST INV"

        if balance_type =='Cash':
            money = Money(amount,'INR')
        elif balance_type =='Gold':
            money = Money(amount,'USD')
        else:
            money = Money(amount,'AUD')

        # using perpetual inventory managent method
        if not revert:
            LedgerTransaction.objects.create_txn(
                journal = self,
                ledgerno = "Sundry Creditors",ledgerno_dr = inv,amount =money
            )
            LedgerTransaction.objects.create_txn(
                journal = self,
                ledgerno =  "Sundry Creditors",ledgerno_dr = "IGST",amount = Money(tax,'INR')
            )
            AccountTransaction.objects.create_txn(
                journal = self,
                ledgerno = "Sundry Creditors",xacttypecode = "Dr",
                xacttypecode_ext = "CRPU",account = account,amount = money + Money(tax,'INR')
            )
            
        else:
            LedgerTransaction.objects.create_txn(
                journal = self,
                ledgerno = inv, ledgerno_dr= "Sundry Creditors", amount=money
            )
            LedgerTransaction.objects.create_txn(
                journal=self,
                ledgerno= "IGST", ledgerno_dr='Sundry Creditors', amount=Money(tax,'INR')
            )
            AccountTransaction.objects.create_txn(
                journal=self,
                ledgerno= "Sundry Creditors", xacttypecode="Cr",
                xacttypecode_ext="AD", account=account, amount=money + Money(tax,'INR')
            )

class PurchaseReturnJournal(Journal):
    base_type = managers.JournalTypes.PR
    objects = managers.PurchaseReturnJournalManager()
    class Meta:
        proxy = True

class PaymentJournal(Journal):
    base_type = managers.JournalTypes.PY
    objects = managers.PaymentJournalManager()
    class Meta:
        proxy = True

    @transaction.atomic()
    def transact(self,revert = False):
        account = self.content_object.supplier.account
        amount = self.content_object.total
        balance_type = self.content_object.type
        cash_ac = Ledger.objects.get(name = 'Cash')
        acc_payable = Ledger.objects.get(name = 'Sundry Creditors')
        cr = TransactionType_DE.objects.get(XactTypeCode ='Cr')
        dr = TransactionType_DE.objects.get(XactTypeCode='Dr')
        pyt = TransactionType_Ext.objects.get(XactTypeCode_ext = 'PYT')
        ca = TransactionType_Ext.objects.get(XactTypeCode_ext='AC')
        if balance_type == 'Cash':
            money = Money(amount,'INR')
        elif balance_type == 'Gold':
            money = Money(amount,'USD')
        else:
            money = Money(amount,'AUD')
        if not revert:
            LedgerTransaction.objects.create(
                journal = self,
                ledgerno = cash_ac,ledgerno_dr = acc_payable,amount =money
            )
            AccountTransaction.objects.create(
                journal = self,
                ledgerno = acc_payable,XactTypeCode = cr,
                XactTypeCode_ext = pyt,
                Account = account,amount = money
            )
        else:
            LedgerTransaction.objects.create(
                journal = self,
                ledgerno=acc_payable, ledgerno_dr=cash_ac, amount=money
            )
            AccountTransaction.objects.create(
                journal = self,
                ledgerno = acc_payable,XactTypeCode = dr,
                XactTypeCode_ext = ca,
                Account = account,amount = money
            )

# postgresql read-only-view
class Ledgerbalance(models.Model):
    ledgerno = models.OneToOneField(Ledger,on_delete = models.DO_NOTHING,primary_key = True)
    name = models.CharField(max_length = 20)
    AccountType = models.CharField(max_length=20)
    created = models.DateTimeField()
    ClosingBalance = ArrayField(MoneyValueField(null = True,blank = True))
    cr =ArrayField(MoneyValueField(null = True,blank = True))
    dr = ArrayField(MoneyValueField(null=True, blank=True))
    class Meta:
        managed = False
        db_table = 'ledger_balance'

    def get_currbal(self):
        return self.get_cb() + self.get_dr() -self.get_cr()

    def get_cb(self):
        return Balance(self.ClosingBalance)
    
    def get_dr(self):
        return Balance(self.dr)

    def get_cr(self):
        return Balance(self.cr)
# how to import ledger and account iniital balance?
    # -- create formset view of corresponding statement sorted by latest

# write a manager method for both acc and ledger that gets txns after self.statement.latest.created


