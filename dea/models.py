from django.db import models,transaction
from django.urls import reverse
from mptt.models import MPTTModel,TreeForeignKey
from django.db.models import Sum
from django.db.models.functions import Coalesce
from contact.models import Customer
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
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
    created = models.DateTimeField(unique = True,auto_now_add = True)
    ClosingBalance = models.DecimalField(max_digits=13, decimal_places=3)
    TotalCredit = models.DecimalField(max_digits=13, decimal_places=3)
    TotalDebit = models.DecimalField(max_digits=13, decimal_places=3)

    class Meta:
        get_latest_by = 'created'

    def __str__(self):
        return f"{self.id}"

# sales,purchase,receipt,payment
class TransactionType_Ext(models.Model):
    XactTypeCode_ext = models.CharField(max_length=3,primary_key= True)
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
    name = models.CharField(max_length=100, unique = True)
    parent = TreeForeignKey('self',
                            null = True,
                            blank = True,
                            on_delete = models.CASCADE,
                            related_name = 'children')

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("dea_ledger_detail", kwargs={"pk": self.pk})
    
    
    def ledger_txn(self,dr_ledger,amount):
        # check if ledger exists
        return LedgerTransaction.objects.create(ledgerno = self,
                                    ledgerno_dr = dr_ledger,
                                    amount=amount)

    def acc_txn(self,ledger,xacttypecode,xacttypecode_ext,amount):
        # check if acc exists
        return AccountTransaction.objects.create(ledgerno = ledger,
                                        XactTypeCode = xacttypecode,
                                        XactTypeCode_ext = xacttypecode_ext,
                                        amount = amount)

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
        credit = self.credit_txns.aggregate(Sum('amount'))
        debit = self.debit_txns.aggregate(Sum('amount'))

        return LedgerStatement.objects.create(self,credit - debit)


    def current_balance(self):
        latest_acc_statement =0
        try:
            latest_acc_statement = self.ledgerstatement_set.latest()
        except:
            print("no recent trxns in this ledger")
        closing_balance = latest_acc_statement.ClosingBalance if latest_acc_statement else 0
        decendants = self.get_descendants(include_self = True)
        bal = [acc.debit_txns.aggregate(t=Coalesce(Sum('amount'), 0))['t']
                 -       
                acc.credit_txns.aggregate(t=Coalesce(Sum('amount'), 0))['t']
                    for acc in decendants]
        return closing_balance + sum(bal)

    def audit(self):
        pass


class Journal(models.Model):

    created = models.DateTimeField(auto_now_add =True)
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

class LedgerTransaction(models.Model):
    journal = models.ForeignKey(Journal,on_delete = models.CASCADE)
    ledgerno = models.ForeignKey(Ledger,on_delete =models.CASCADE ,related_name='credit_txns')
    created = models.DateTimeField(unique = True, auto_now_add = True)
    ledgerno_dr = models.ForeignKey(Ledger ,on_delete =models.CASCADE, related_name= 'debit_txns')
    amount = models.DecimalField(max_digits=13, decimal_places=3)

    def __str__(self):
        return self.ledgerno.name

class LedgerStatement(models.Model):
    ledgerno = models.ForeignKey(Ledger,on_delete = models.CASCADE)
    created = models.DateTimeField(unique = True,auto_now_add=True)
    ClosingBalance = models.DecimalField(max_digits=13, decimal_places=3)

    class Meta:
        get_latest_by = 'created'

    def __str__(self):
        return f"{self.created} - {self.ClosingBalance}"


class AccountTransaction(models.Model):
    journal = models.ForeignKey(Journal,on_delete = models.CASCADE)
    ledgerno = models.ForeignKey(Ledger,on_delete = models.CASCADE)
    created = models.DateTimeField(auto_now_add= True,unique = True)
    XactTypeCode = models.ForeignKey(TransactionType_DE,
                    on_delete = models.CASCADE)
    XactTypeCode_ext = models.ForeignKey(TransactionType_Ext,
                        on_delete=models.CASCADE)
    Account = models.ForeignKey(Account,on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=13,decimal_places=3)

    def __str__(self):
        return f"{self.XactTypeCode_ext}"

# proxy models for all types of journals
# all journals to be seperated into another file figure out how
from .managers import (LoanGivenJournalManager,LoanTakenJournalManager,
                        LoanReleaseJournalmanager,LoanRepayJournalmanager)

class LoanJournal(Journal):
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

# add a way to import ledger and account iniital balance
# i.e import each bal to corresponding acc by creating that particulat statement with closing balance

# add a way to initiate audit

# add a view to view current balance since audit

# statements are only created when user select audit report

# otherwise statements are created manually for inputting opening balance

# a common function audit_all() to audit ledger and accounts i.e report daybook or something like that
# for acc and ledger get txns after statement if any
# write a manager method for both acc and ledger that gets txns after self.statement.latest.created


