import django_tables2 as tables
from django_tables2.utils import A
from .models import Loan,Release

class CheckBoxColumnWithName(tables.CheckBoxColumn):
    @property
    def header(self):
        return self.verbose_name

class LoanTable(tables.Table):

    loanid=tables.LinkColumn('girvi_loan_detail',args=[A('pk')])
    # release = tables.LinkColumn('girvi_release_create', args=[A('id')],attrs={'a':{"class":"btn btn-outline-info","role":"button"}}, orderable=False, empty_values=())
    cbox = CheckBoxColumnWithName(verbose_name="*", accessor='pk')
    # def render_release(self):
    #     return 'Release'
    def render_created(self,value):
        return value.date

    # Increases sql queries count to 118
    # def render_id(self, value, column):
    #     # if value.release__isnull:
    #     if Release.objects.filter(loan_id=value).exists():
    #         column.attrs = {'td': {'bgcolor': 'lightgreen'}}
    #     else:
    #         column.attrs = {'td': {}}
    #     return value
    class Meta:
        model = Loan
        fields = ('id','cbox','series','loanid','created','customer','itemdesc','itemweight','loanamount')
        attrs = {"class":"table table-sm table-striped table-bordered table-hover"}
        empty_text = "There are no customers matching the search criteria..."
        template_name = 'django_tables2/bootstrap4.html'

class ReleaseTable(tables.Table):
    releaseid = tables.LinkColumn('girvi_release_detail',args=[A('pk')])

    class Meta:
        model = Release
        fields=('id','releaseid','created','loan','interestpaid')
        attrs={"class":"table table-sm table-striped table-bordered table-hover"}
        empty_text = "There are no customers matching the search criteria..."
        # template_name = 'django_tables2/bootstrap4.html'
