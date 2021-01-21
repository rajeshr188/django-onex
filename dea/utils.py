from .models import (Account,Ledger,LedgerTransaction,AccountTransaction, 
                        TransactionType_DE,TransactionType_Ext)

cr = TransactionType_DE.objects.get(XactTypeCode='Cr')
dr = TransactionType_DE.objects.get(XactTypeCode='Dr')

lt = TransactionType_Ext.objects.get(XactTypeCode_ext='LT')
lg = TransactionType_Ext.objects.get(XactTypeCode_ext='LG')

cash_ledger_Acc = Ledger.objects.get(name="Cash In Drawer")
liability_loan = Ledger.objects.get(name="LoansTaken")
