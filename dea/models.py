import decimal
from django.db import models,transaction,connection
from django.contrib.postgres.fields import ArrayField
from django.urls import reverse
from moneyed.classes import Currency
from mptt.models import MPTTModel,TreeForeignKey
from django.db.models import Sum
from django.db.models.functions import Coalesce
from contact.models import Customer
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from djmoney.models.fields import MoneyField
from moneyed import Money
from .utils.currency import Balance
from psycopg2.extras import register_composite
from psycopg2.extensions import register_adapter, adapt, AsIs

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
        # in input box we enter 10 USD,20 INR,30 AUD
        amount,currency = value.split()
        return Money(amount,currency)
        
    def db_type(self,connection):
        return 'money_value'

# Create your models here.

# class BalanceType(models.Model):
#     name = models.CharField(max_length = 10)

#     def __str__(self):
#         return self.name

# class Balance(models.Model):
#     type = models.models.ForeignKey("dea.BalanceType", on_delete=models.CASCADE)
#     total = models.DecimalField(max_digits=11, decimal_places=3)

#     class Meta:
#         abstract = True
#     def __str__(self):
#         return f"{self.type}:{self.total}"

# class LedgerBalance(Balance):
#     ledger = models.ForeignKey("dea.Ledger", on_delete=models.CASCADE)

# class AccountBalance(Balance):
#     acc = models.ForeignKey('Account', on_delete = models.CASCADE)

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
                        on_delete = models.SET_NULL)
    AccountType_Ext = models.ForeignKey(AccountType_Ext,
                        on_delete = models.CASCADE)

    contact = models.OneToOneField(Customer,
                        on_delete = models.CASCADE,
                        )

    def __str__(self):
        return self.contact.name
        
    def get_absolute_url(self):
        return reverse("dea_account_detail", kwargs={"pk": self.pk})
    
    def set_opening_bal(self,amount,tc=0,tb=0):
        # ensure there aint no txns before setting op bal if present then audit and adjust
        return AccountStatement.objects.create(self,amount,0,0)

    def adjust(self,amount,xacttypecode):
        pass

    def audit(self):
        try:
            latest_stmt = AccountStatement.objects.latest()
        except:
            latest_stmt = None

        if latest_stmt:
            cb = self.current_balance(since = latest_stmt.created)
        else:
            cb = self.current_balance()
        return AccountStatement.objects.create(self,cb,self.total_credit,self.total_debit)

    def total_credit(self):
        try:
            ls = AccountStatement.object.latest()
            return self.accounttransaction_set.filter(created_ge = ls.created,
                XactTypeCode__XactTypeCode='Cr').\
                aggregate(t=Sum('Amount')).t
        except:
            ls=None
            return self.accounttransaction_set.filter(XactTypeCode__XactTypeCode = 'Cr').\
                    aggregate(t = Sum('Amount')).t
        
    def total_debit(self):
        try:
            ls = AccountStatement.object.latest()
            return self.accounttransaction_set.filter(created_ge=ls.created,
                                                      XactTypeCode__XactTypeCode='Dr').\
                aggregate(t=Sum('Amount')).t
        except:
            ls = None
            return self.accounttransaction_set.filter(XactTypeCode__XactTypeCode='Dr').\
                aggregate(t=Sum('Amount')).t

    def current_balance(self,since = None):

        latest_acc_stmt = 0
        try:
            latest_acc_stmt = self.accountstatement_set.latest()
        except:
            print("no acc statement available")
        closing_balance = latest_acc_stmt.ClosingBalance if latest_acc_stmt else 0
        
        credit = self.accounttransaction_set\
                    .filter(XactTypeCode_ext__in = ['LT','LR','IR'])\
                    .aggregate(
                    t = Coalesce(Sum('amount'),0))
        
        debit = self.accounttransaction_set\
                    .filter(XactTypeCode_ext__in = ['LG','LP','IP'])\
                    .aggregate(
                    t=Coalesce(Sum('amount'),0))
        
        return closing_balance + (credit['t'] - debit['t'])

# account statement for ext account
class AccountStatement(models.Model):
    AccountNo = models.ForeignKey(Account,
                        on_delete = models.CASCADE)
    created = models.DateTimeField(unique = True, auto_now_add = True)
    ClosingBalance = ArrayField(MoneyValueField(null = True,blank = True))
    TotalCredit = ArrayField(MoneyValueField(null = True,blank = True))
    TotalDebit = ArrayField(MoneyValueField(null=True, blank=True))
    # ClosingBalance = models.DecimalField(max_digits=13, decimal_places=3)
    # TotalCredit = models.DecimalField(max_digits=13, decimal_places=3)
    # TotalDebit = models.DecimalField(max_digits=13, decimal_places=3)

    class Meta:
        get_latest_by = 'created'

    def __str__(self):
        return f"{self.id}"

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

    class MPTTMeta:
        order_insertion_by = ['name']
        constraints = [
        models.UniqueConstraint(fields=['name', 'parent'], name='unique ledgername-parent')
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("dea_ledger_detail", kwargs={"pk": self.pk})
    
    
    def ledger_txn(self,dr_ledger,amount):
        # check if ledger exists
        return LedgerTransaction.objects.create(ledgerno = self,
                                    ledgerno_dr = dr_ledger,
                                    amount=amount)

    # def acc_txn(self,ledger,xacttypecode,xacttypecode_ext,amount):
    #     # check if acc exists
    #     return AccountTransaction.objects.create(ledgerno = ledger,
    #                                     XactTypeCode = xacttypecode,
    #                                     XactTypeCode_ext = xacttypecode_ext,
    #                                     amount = amount)

    def set_opening_bal(self,amount):
        # ensure there aint no txns before setting op bal if present then audit and adjust

        return LedgerStatement.objects.create(self,amount)

    def adjust(self,xacttypcode,amount):
        pass
    
    def audit(self):
        
        # get latest audit
        # then get txns after latest audit
        # then crunch debit and credit and find closing bal
        # then save that closing bal as latest statement 
        # this statement will serve as opening balance for this acc

        # credit = self.credit_txns.aggregate(Sum('amount'))
        # debit = self.debit_txns.aggregate(Sum('amount'))

        # return LedgerStatement.objects.create(self,credit - debit)
        credit_bal = Balance([Money(r["total"], r["amount_currency"]) 
                        for r in self.debit_txns.annotate(total = Sum("amount"))])
        debit_bal = Balance([Money(r["total"], r["amount_currency"])
                             for r in self.credit_txns.annotate(total=Sum("amount"))])
        return debit_bal - credit_bal

    def current_balance(self):

        latest_acc_statement =0

        try:
            latest_acc_statement = self.ledgerstatement_set.latest()
        except:
            print("no recent trxns in this ledger")

        closing_balance = Balance(latest_acc_statement.ClosingBalance) if latest_acc_statement else Balance()
        decendants = self.get_descendants(include_self = True)

        bal = [Balance([Money(r["total"], r["amount_currency"]) 
                        for r in acc.debit_txns.annotate(total = Sum("amount"))])
                - 
               Balance([Money(r["total"], r["amount_currency"])
                        for r in acc.credit_txns.annotate(total = Sum("amount"))])
                for acc in decendants
                ]
        # bal = [acc.debit_txns.aggregate(t=Coalesce(Sum('amount'), 0))['t']
        #          -       
        #         acc.credit_txns.aggregate(t=Coalesce(Sum('amount'), 0))['t']
        #             for acc in decendants]
        # return closing_balance + sum(bal)
        return sum(bal,closing_balance)

    def audit(self):
        pass


class Journal(models.Model):

    created = models.DateTimeField(auto_now_add =True)
    class Types(models.TextChoices):
        BJ = "Base Journal","base journal"
        SJ = "Sales Journal","Sales journal"
        LJ = "Loan Journal","Loan journal"
        PJ = "Purchase Journal","Purchase journal"
        LT = "Loan Taken","Loan taken"
        LG = "Loan Given","Loan given"
        LR = "Loan Released","Loan released"
        LP = "Loan Paid","Loan paid"
    base_type = Types.SJ
    type = models.CharField(max_length = 50,choices = Types.choices,default = base_type)
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

class LedgerTransaction(models.Model):
    journal = models.ForeignKey(Journal,on_delete = models.CASCADE)
    ledgerno = models.ForeignKey(Ledger,on_delete =models.CASCADE ,related_name='credit_txns')
    created = models.DateTimeField(unique = True, auto_now_add = True)
    ledgerno_dr = models.ForeignKey(Ledger ,on_delete =models.CASCADE, related_name= 'debit_txns')
    # amount = models.DecimalField(max_digits=13, decimal_places=3)
    amount = MoneyField(max_digits=13,decimal_places=3,default_currency='INR')

    def __str__(self):
        return self.ledgerno.name

class LedgerStatement(models.Model):
    ledgerno = models.ForeignKey(Ledger,on_delete = models.CASCADE)
    created = models.DateTimeField(unique = True,auto_now_add=True)
    # ClosingBalance = models.DecimalField(max_digits=13, decimal_places=3)
    ClosingBalance = ArrayField(MoneyValueField(null=True, blank=True))
    
    class Meta:
        get_latest_by = 'created'

    def __str__(self):
        return f"{self.created.date()} - {self.ledgerno} - {self.ClosingBalance}"

    def get_cb(self):
        return Balance(self.ClosingBalance)


class AccountTransaction(models.Model):
    journal = models.ForeignKey(Journal,on_delete = models.CASCADE)
    ledgerno = models.ForeignKey(Ledger,on_delete = models.CASCADE)
    created = models.DateTimeField(auto_now_add= True,unique = True)
    XactTypeCode = models.ForeignKey(TransactionType_DE,
                    on_delete = models.CASCADE)
    XactTypeCode_ext = models.ForeignKey(TransactionType_Ext,
                        on_delete=models.CASCADE)
    Account = models.ForeignKey(Account,on_delete=models.CASCADE)
    # amount = models.DecimalField(max_digits=13,decimal_places=3)
    amount = MoneyField(max_digits=13,decimal_places=3,default_currency='INR')

    def __str__(self):
        return f"{self.XactTypeCode_ext}"

# proxy models for all types of journals
# all journals to be seperated into another file figure out how
from .managers import (LoanGivenJournalManager,LoanTakenJournalManager,
                        LoanReleaseJournalmanager,LoanRepayJournalmanager)

class LoanJournal(Journal):
    base_type = Journal.Types.LJ
    loanstaken = LoanTakenJournalManager()
    loansgiven = LoanGivenJournalManager()
    loanreleased = LoanReleaseJournalmanager()
    loanrepaid = LoanRepayJournalmanager()

    class Meta:
        proxy = True
    
    @transaction.atomic()
    def pledge_loan(self, account, amount):
        asset_loan = Ledger.objects.get(name="LoansGiven")
        cash_ledger_Acc = Ledger.objects.get(name="Cash In Drawer")
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

    @transaction.atomic()
    def take_loan(self,account,amount):
    
        liability_loan = Ledger.objects.get(name = 'LoansTaken')
        cash_ledger_Acc = Ledger.objects.get(name = 'Cash In Drawer')
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

    @transaction.atomic()
    def pay_interest(self,account,amount):
        ip = TransactionType_Ext.objects.get(XactTypeCode_ext='IP')
        int_paid = Ledger.objects.get(name='Interest Paid')
        int_payable = Ledger.objects.get(name='Interest Payable')
        cash_ledger_Acc = Ledger.objects.get(name="Cash In Drawer")
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

    @transaction.atomic()
    def receive_interest(self, account, interest):
        int_received = Ledger.objects.get(name="Interest Received")
        cash_ledger_Acc = Ledger.objects.get(name="Cash In Drawer")
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

    @transaction.atomic()
    def release(self, account, amount):
        cash_ledger_Acc = Ledger.objects.get(name="Cash In Drawer")
        lr = TransactionType_Ext.objects.get(XactTypeCode_ext='LR')
        dr = TransactionType_DE.objects.get(XactTypeCode='Dr')

        asset_loan = Ledger.objects.get(name="LoansGiven")
        LedgerTransaction.objects.create(
            journal=self,
            ledgerno=asset_loan, ledgerno_dr=cash_ledger_Acc, amount=amount
        )
        AccountTransaction.objects.create(
            journal=self,
            ledgerno=asset_loan, XactTypeCode=dr,
            XactTypeCode_ext=lr, Account=account, amount=amount
        )

    @transaction.atomic()
    def repay(self, account, amount):
        lp = TransactionType_Ext.objects.get(XactTypeCode_ext='LP')
        cr = TransactionType_DE.objects.get(XactTypeCode='Cr')
        cash_ledger_acc = Ledger.objects.get(name="Cash In Drawer")

        if self.AccountType_Ext.description == "Creditor":
            liability_loan = Ledger.objects.get(name="LoansTaken")

            AccountTransaction.objects.create(
                journal=self,
                ledgerno=liability_loan, XactTypeCode=cr,
                XactTypeCode_ext=lp, Account=account, amount=amount)

            LedgerTransaction.objects.create(
                journal=self,
                ledgerno=cash_ledger_acc,
                ledgerno_dr=liability_loan, amount=amount)

class SalesJournal(Journal):
    base_type = Journal.Types.SJ
    class Meta:
        proxy = True

    def sale(self,account,amount,payment_term,balance_type):
        # payment_term[Cash,Credit]
        # balance_type[Cash,Gold]
        cr = TransactionType_DE.objects.get(XactTypeCode = 'Cr')
        sl_cash = TransactionType_Ext.objects.get(XactTypeCode_ext = 'slh')
        sl_credit = TransactionType_Ext.objects.get(XactTypeCode_ext = 'slc')

        if payment_term == 'Cash':
            cash_acc = Ledger.objects.get(name=balance_type,parent__name = 'Cash In Drawer')
            debit_ac = cash_acc
            txn_ext = sl_cash
        else:
            acc_receivable = Ledger.objects.get(name=balance_type,parent__name = 'Accounts Receivable')
            debit_ac = acc_receivable
            txn_ext = sl_credit

        # cash/gold
        revenue_acc = Ledger.objects.get(name = balance_type,parent__name = 'Revenue')
        inventory = Ledger.objects.get(name=balance_type,parent__name = 'Inventory')
        COGS = Ledger.objects.get(name =balance_type,parent__name =  'COGS')   

        LedgerTransaction(
                journal=self,
                ledgeno = revenue_acc,ledgeno_dr = debit_ac,amount = amount)
        LedgerTransaction(
                journal=self,
                ledgerno = inventory,ledgerno_dr = COGS ,amount = amount
            )

        AccountTransaction.objects.create(
            journal = self,
            ledgerno = revenue_acc,XactTypeCode = cr,
            XactTypeCode_ext = txn_ext,Account = account,amount = amount
        )
    def sale_return():
        pass
    def Receipt(self,account,amount,balance_type):
        cash_ac = Ledger.objects.get(name = balance_type,parent__name ='Cash In Drawer')
        acc_recv = Ledger.objects.get(name = balance_type,parent__name = 'Accounts Receivable')
        cr = TransactionType_DE.objects.get(XactTypeCode ='Cr')
        sre = TransactionType_Ext.objects.get(XactTypeCode_ext = 'SRE')
        LedgerTransaction.objects.create(
            journal = self,
            ledgerno = acc_recv,ledgerno_dr = cash_ac,amount = amount
        )
        AccountTransaction.objects.create(
            journal = self,
            ledgerno = acc_recv,XactTypeCode =cr,
            XactTypeCode_ext =sre, Account = account,amount = amount
        )

class PurchaseJournal(Journal):
    base_type = Journal.Types.PJ
    class Meta:
        proxy =True

    @transaction.atomic()
    def purchase(self,account,amount,payment_term,balance_type):
        purch_exp = Ledger.objects.get(name=balance_type,parent__name ='COGP')
        cash_ac = Ledger.objects.get(name=balance_type,parent__name = 'Cash In Drawer')
        acc_payable = Ledger.objects.get(name =balance_type,parent__name = 'Accounts Payables')
        cr = TransactionType_DE.objects.get(XactTypeCode = 'Cr')
        
        if payment_term == 'Cash':
            credit_ac = cash_ac
            txn_ext = TransactionType_Ext.objects.get(XactTypeCode_ext = 'CPU')
        else:
            credit_ac = acc_payable
            txn_ext = TransactionType_Ext.objects.get(XactTypeCode_ext = 'CRPU')
        LedgerTransaction.objects.create(
            journal = self,
            ledgerno = credit_ac,ledgerno_dr = purch_exp,amount =amount
        )
        AccountTransaction.objects.create(
            journal = self,
            ledgerno = cash_ac,XactTypeCode = cr,
            XactTypeCode_ext = txn_ext,Account = account,amount = amount
        )

    @transaction.atomic()
    def purchase_return():
        pass

    @transaction.atomic()
    def Payment(self,account,amount,balance_type):
        cash_ac = Ledger.objects.get(name =balance_type,parent__name = 'Cash In Drawer')
        acc_payable = Ledger.objects.get(name=balance_type,parent__name = 'Accounts Payables')
        dr = TransactionType_DE.objects.get(XactTypeCode ='Dr')

        LedgerTransaction.objects.create(
            journal = self,
            ledgerno = cash_ac,ledgerno_dr = acc_payable,amount =amount
        )
        AccountTransaction.objects.create(
            journal = self,
            ledgerno = acc_payable,XactTypeCode = dr,
            Account = account,amount = amount
        )

# add a way to import ledger and account iniital balance
# i.e import each bal to corresponding acc by creating that particulat statement with closing balance

# add a way to initiate audit

# add a view to view current balance since audit

# statements are only created when user select audit report

# otherwise statements are created manually for inputting opening balance

# a common function audit_all() to audit ledger and accounts i.e report daybook or something like that
# for acc and ledger get txns after statement if any
# write a manager method for both acc and ledger that gets txns after self.statement.latest.created


