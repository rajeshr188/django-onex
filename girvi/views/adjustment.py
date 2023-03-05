from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, UpdateView
from django_filters.views import FilterView
from django_tables2.export.views import ExportMixin
from django_tables2.views import SingleTableMixin

from ..filters import AdjustmentFilter
from ..forms import AdjustmentForm
from ..models import Adjustment, Loan


class AdjustmentListView(LoginRequiredMixin, ExportMixin, SingleTableMixin, FilterView):
    # table_class=AdjustmentTable
    model = Adjustment
    filterset_class = AdjustmentFilter
    paginate_by = 50


class AdjustmentCreateView(LoginRequiredMixin, CreateView):
    model = Adjustment
    form_class = AdjustmentForm
    success_url = "girvi_loan_detail"

    def get_initial(self):
        if self.kwargs:
            loan = Loan.objects.get(id=self.kwargs["pk"])
            return {
                "loan": loan,
            }

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class AdjustmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Adjustment
    form_class = AdjustmentForm


class AdjustmentDeleteView(LoginRequiredMixin, DeleteView):
    model = Adjustment
    success_url = reverse_lazy("girvi_adjustments_list")
