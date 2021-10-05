import django_tables2 as tables
from .models import Accountbalance,Ledgerbalance

class AccountbalanceTable(tables.Table):
    acc_name = tables.Column(linkify=('dea_account_detail', [tables.A("pk")]),
                             empty_values=(),
                             )
    def render_ClosingBalance(self,record):
        return record.get_cb()
    
    class Meta:
        model = Accountbalance
        fields = ['entity','acc_type','acc_name','AccountNo','TotalCredit','TotalDebit','ClosingBalance']
        attrs = {"class": "table table-sm text-center  table-striped table-bordered"}
        empty_text = "There are no Accounts matching the search criteria..."
        template_name = 'django_tables2/bootstrap4.html'

class LedgerbalanceTable(tables.Table):
    pass
