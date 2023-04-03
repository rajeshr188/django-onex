from dea.models import Ledger

def create_loan_journal(loan):
    try:
        loan.customer.account
    except:
        loan.customer.save()
    amount = Money(loan.loanamount, "INR")
    interest = Money(loan.interest_amt(), "INR")
    if loan.customer.type == "Su":
        
        jrnl = Journal.objects.create(
            type=JournalTypes.LT, content_object=loan, desc="Loan Taken"
        )
        lt = [
            {"ledgerno": "Loans", "ledgerno_dr": "Cash", "amount": amount},
            {"ledgerno": "Cash", "ledgerno_dr": "Interest Paid", "amount": amount},
        ]
        at = [
            {
                "ledgerno": "Loans",
                "Xacttypecode": "Dr",
                "xacttypecode_ext": "LT",
                "account": loan.customer.account,
                "amount": amount,
            },
            {
                "ledgerno": "Interest Payable",
                "xacttypecode": "Cr",
                "xacttypecode_ext": "IP",
                "account": loan.customer.account,
                "amount": amount,
            },
        ]
    else:
        jrnl = Journal.objects.create(
            type=JournalTypes.LG, content_object=loan, desc="Loan Given"
        )
        lt = [
            {
                "ledgerno": "Cash",
                "ledgerno_dr": "Loans & Advances",
                "amount": amount,
            },
            {
                "ledgerno": "Interest Received",
                "ledgerno_dr": "Cash",
                "amount": interest,
            },
        ]
        at = [
            {
                "ledgerno": "Loans & Advances",
                "xacttypecode": "Cr",
                "xacttypecode_ext": "LG",
                "account": loan.customer.account,
                "amount": amount,
            },
            {
                "ledgerno": "Interest Received",
                "xacttypecode": "Dr",
                "xacttypecode_ext": "IR",
                "account": loan.customer.account,
                "amount": interest,
            },
        ]
    jrnl.transact(lt, at)

def create_release_journal(release):
    amount = Money(self.loan.loanamount, "INR")
    interest = Money(self.interestpaid, "INR")
    if self.customer.type == "Su":
        jrnl = Journal.objects.create(content_object=self, desc="Loan Repaid")
        lt = [
            {"ledgerno": "Cash", "ledgerno_dr": "Loans", "amount": amount},
            {"ledgerno": "Cash", "ledgerno_dr": "Interest Paid", "amount": amount},
        ]
        at = [
            {
                "ledgerno": "Loans",
                "xacttypecode": "Cr",
                "xacttypecode_ext": "LP",
                "account": self.customer.account,
                "amount": amount,
            },
            {
                "ledgerno": "Interest Payable",
                "xacttypecode": "Cr",
                "xacttypecode_ext": "IP",
                "account": self.customer.account,
                "amount": amount,
            },
        ]
    else:
        jrnl = Journal.objects.create(content_object=self, desc="Loan Released")
        lt = [
            {
                "ledgerno": "Loans & Advances",
                "ledgerno_dr": "Cash",
                "amount": amount,
            },
            {
                "ledgerno": "Interest Received",
                "ledgerno_dr": "Cash",
                "amount": amount,
            },
        ]
        at = [
            {
                "ledgerno": "Loans & Advances",
                "xacttypecode": "Dr",
                "xacttypecode_ext": "LR",
                "account": self.customer.account,
                "amount": amount,
            },
            {
                "ledgerno": "Interest Received",
                "xacttypecode": "Dr",
                "xacttypecode_ext": "IR",
                "account": self.customer.account,
                "amount": interest,
            },
        ]
    jrnl.transact(lt, at)

def create_adjustment_journal(adjustment):
    """
    loan adjustment can be applied to principal or interest
    loan adjustment involves Loans and Interest PAyable if customer is supplier
    else Loans & Advances and Interest Received if customer is regular
    """
    amount = Money(self.amount_received, "INR")
    if adjustment.as_interest:
        jrnl_desc = "Loan Interest Adjustment"
        ledgerno_dr = "Interest Payable" if adjustment.customer.customer_type == 'Re' else "Interest Received"
    else:
        jrnl_desc = "Loan Principle Adjustment"
        ledgerno_dr = "Loans" if adjustment.customer.customer_type == 'Re' else "Loans & Advances"
        
     jrnl = Journal.objects.create(content_object=self, desc="Loan Adjustment")
    
    lt = [
        {"ledgerno": "Cash", "ledgerno_dr": ledgerno_dr, "amount": amount},]
    at = [
        {
            "ledgerno": "Interest Payable",
            "xacttypecode": "Dr",
            "xacttypecode_ext": "IP",
            "account": self.customer.account,
            "amount": amount,
        },
    ]
    
    jrnl.transact(lt, at)

def create_sales_journal(sale):
    jrnl = Journal.objects.create(
                type=JournalTypes.SJ, content_object=self, desc="sale"
            )

    inv = "GST INV" if self.is_gst else "Non-GST INV"
    cogs = "GST COGS" if self.is_gst else "Non-GST COGS"
    money = Money(self.balance, self.balancetype)
    tax = Money(self.get_gst(), "INR")
    lt = [
        {"ledgerno": "Sales", "ledgerno_dr": "Sundry Debtors", "amount": money},
        {"ledgerno": inv, "ledgerno_dr": cogs, "amount": money},
    ]
    if sale.is_gst:
        lt.append({
            "ledgerno": "Output Igst",
            "ledgerno_dr": "Sundry Debtors",
            "amount": tax,
        })
    at = [
        {
            "ledgerno": "Sales",
            "xacttypecode": "Cr",
            "xacttypecode_ext": "CRSL",
            "account": self.customer.account,
            "amount": money + tax,
        }
    ]
    jrnl.transact(lt, at)

def create_receipt_journal(receipt):
    jrnl = Journal.objects.create(
                content_object=self, type=JournalTypes.RC, desc="Receipt"
            )
    money = Money(self.total, self.type)
    lt = [
        {"ledgerno": "Sundry Debtors", "ledgerno_dr": "Cash", "amount": money}
    ]
    at = [
        {
            "ledgerno": "Sundry Debtors",
            "xacttypecode": "Dr",
            "xacttypecode_ext": "RCT",
            "account": self.customer.account,
            "amount": money,
        }
    ]
    jrnl.transact(lt, at)

def create_purchase_journal(purchase):
    
    jrnl = Journal.objects.create(type=JournalTypes.PJ,
                    content_object=self, desc='purchase')
    
    ledgers = dict(list(Ledger.objects.values_list('name', 'id')))
    money = Money(self.balance, self.balancetype)
    try:
        self.supplier.account
    except:
        self.supplier.save()
    if self.is_gst:
        inv = ledgers["GST INV"]
        tax = Money(self.get_gst(), 'INR')
        amount = money + tax
    else:
        inv = ledgers["Non-GST INV"]
        amount = money
        tax = Money(0,'INR')

    lt = [
            {'ledgerno': ledgers['Sundry Creditors'],'ledgerno_dr':inv,'amount':money},
            {'ledgerno': ledgers['Sundry Creditors'], 'ledgerno_dr': ledgers['Input IGST'], 'amount': tax}, 
        ]
    at = [
            {'ledgerno': ledgers['Sundry Creditors'],'xacttypecode':'Dr','xacttypecode_ext':'CRPU',
                'account':self.supplier.account.id, 'amount':amount}
        ]
 
    jrnl.transact(lt,at)
    return jrnl

def create_payment_jounral(payment):
    jrnl = Journal.objects.create(type = JournalTypes.PY,
                content_object = self,
                desc = 'payment')
            
    money = Money(self.total, self.type)
    lt = [{'ledgerno':ledgers['Cash'],'ledgerno_dr':ledgers['Sundry Creditors'],'amount':money}]
    at = [{'ledgerno':ledgers['Sundry Creditors'],'xacttypecode':'Cr','xacttypecode_ext':'PYT',
            'account':self.supplier.account.id,'amount':money}]
    jrnl.transact(lt,at)
    return jrnl