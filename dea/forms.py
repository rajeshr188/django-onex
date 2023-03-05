from django import forms

from .models import Account, AccountStatement, Ledger, LedgerStatement


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = "__all__"


class AccountStatementForm(forms.ModelForm):
    class Meta:
        model = AccountStatement
        fields = ("AccountNo", "ClosingBalance", "TotalCredit", "TotalDebit")


class LedgerForm(forms.ModelForm):
    class Meta:
        model = Ledger
        fields = "__all__"


class LedgerStatementForm(forms.ModelForm):
    class Meta:
        model = LedgerStatement
        fields = ("ledgerno", "ClosingBalance")


# op bal foormset for ledger and acc
