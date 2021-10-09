from django import forms
from .models import Journal, Ledger, Account, LedgerStatement, AccountStatement


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = '__all__'


class AccountStatementForm(forms.ModelForm):
    class Meta:
        model = AccountStatement
        fields = ('AccountNo', 'ClosingBalance', 'TotalCredit', 'TotalDebit')


class LedgerForm(forms.ModelForm):
    class Meta:
        model = Ledger
        fields = '__all__'


class LedgerStatementForm(forms.ModelForm):
    class Meta:
        model = LedgerStatement
        fields = ('ledgerno', 'ClosingBalance')

class JournalForm(forms.ModelForm):
    class Meta:
        model = Journal
        fields = ('type','desc')

# op bal foormset for ledger and acc
