from typing import List

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from django_filters.views import FilterView
from django_tables2.export.views import ExportMixin
from django_tables2.views import SingleTableMixin

# from utils.render import Render

from ..filters import ReleaseFilter
from ..forms import BulkReleaseForm, ReleaseForm
from ..models import Loan, Release
from ..tables import ReleaseTable


def increlid():
    last = Release.objects.all().order_by("id").last()
    if not last:
        return "1"
    return str(int(last.releaseid) + 1)


class ReleaseListView(LoginRequiredMixin, ExportMixin, SingleTableMixin, FilterView):
    table_class = ReleaseTable
    model = Release
    filterset_class = ReleaseFilter
    template_name = "girvi/release_list.html"
    paginate_by = 10

    def get_template_names(self) -> List[str]:
        if self.request.META.get("HTTP_HX_REQUEST"):
            self.template_name = "girvi/partials/release_list_view.html"
        return super().get_template_names()


class ReleaseCreateView(LoginRequiredMixin, CreateView):
    model = Release
    form_class = ReleaseForm

    def get_initial(self):
        if self.kwargs:
            loan = Loan.objects.get(id=self.kwargs["pk"])
            return {
                "releaseid": increlid,
                "loan": loan,
                "interestpaid": loan.interestdue,
            }

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ReleaseDetailView(LoginRequiredMixin, DetailView):
    model = Release


class ReleaseUpdateView(LoginRequiredMixin, UpdateView):
    model = Release
    form_class = ReleaseForm


class ReleaseDeleteView(LoginRequiredMixin, DeleteView):
    model = Release
    success_url = reverse_lazy("girvi_release_list")


def post_release(request, pk):
    release = get_object_or_404(Release, pk=pk)
    if not release.posted:
        release.post()
    return redirect(release)


def unpost_release(request, pk):
    release = get_object_or_404(Release, pk=pk)
    if release.posted:
        release.unpost()
    return redirect(release)


# @login_required
# def print_release(request, pk):
#     release = Release.objects.get(id=pk)
#     params = {"release": release}
#     return Render.render("girvi/release_pdf.html", params)


from django.db import IntegrityError


def bulk_release(request):
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = BulkReleaseForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            date = form.cleaned_data["date"]
            loans = form.cleaned_data["loans"]

            if not date:
                date = timezone.now().date()

            for loan in loans:
                try:
                    l = Loan.objects.get(loanid=loan.loanid)
                except Loan.DoesNotExist:
                    # raise CommandError(f"Failed to create Release as {loan} does not exist")
                    print(f"Failed to create Release as {loan} does not exist")
                    continue
                try:
                    releaseid = Release.objects.order_by("-id")[0]
                    releaseid = str(int(releaseid.releaseid) + 1)
                    r = Release.objects.create(
                        releaseid=releaseid,
                        loan=l,
                        created=date,  # datetime.now(timezone.utc),
                        interestpaid=l.interestdue(date),
                        created_by=request.user,
                    )
                except IntegrityError:
                    # raise CommandError(f"Failed creating Release as {l} is already Released with {l.release}")
                    print(
                        f"Failed creating Release as {l} is already Released with {l.release}"
                    )
    # if a GET (or any other method) we'll create a blank form
    else:
        selected_loans = request.GET.getlist("selection", "")
        qs = Loan.unreleased.filter(id__in=selected_loans).values_list("id", flat=True)
        form = BulkReleaseForm(initial={"loans": qs})
    return render(request, "girvi/bulk_release.html", {"form": form})
