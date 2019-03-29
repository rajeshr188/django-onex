import django_tables2 as tables
from django_tables2.utils import A
from .models import Loan,Release

class LoanTable(tables.Table):
    loanid=tables.LinkColumn('girvi_loan_detail',args=[A('pk')])
    # status = tables.Column(accessor='get_total_receipts',verbose_name="Paid",orderable=False)
    class Meta:
        model = Loan
        fields = ('id','license','loanid','created','customer','itemtype','itemdesc','itemweight','loanamount','interestrate')
        attrs = {"class":"table table-sm table-striped table-bordered table-hover"}
        empty_text = "There are no customers matching the search criteria..."
        template_name = 'django_tables2/bootstrap4.html'

class ReleaseTable(tables.Table):
    releaseid = tables.LinkColumn('girvi_release_detail',args=[A('pk')])
    
    class Meta:
        model = Release
        fields=('id','releaseid','created','customer','loan','interestpaid')
        attrs={"class":"table table-sm table-striped table-bordered table-hover"}
        empty_text = "There are no customers matching the search criteria..."
        template_name = 'django_tables2/bootstrap4.html'
