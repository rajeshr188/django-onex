from django_filters.views import FilterView
from django_tables2.export.views import ExportMixin
from django_tables2.views import SingleTableMixin
from num2words import num2words
from django.views.generic import CreateView
from ..filters import PaymentFilter
from ..forms import PaymentForm
from ..models import Payment

# from ..render import Render
from ..tables import PaymentTable

# def print_payment(pk):
#     payment = Payment.objects.get(id=pk)
#     params = {"payment": payment, "inwords": num2words(payment.total, lang="en_IN")}
#     return Render.render("purchase/payment.html", params)


class PaymentListView(ExportMixin, SingleTableMixin, FilterView):
    model = Payment
    table_class = PaymentTable
    filterset_class = PaymentFilter
    template_name = "purchase/payment_list.html"
    paginate_by = 25


class PaymentCreateView(CreateView):
    model = Payment
    form_class = PaymentForm

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        paymentitem_form = PaymentItemFormSet()

        return self.render_to_response(
            self.get_context_data(form=form,
                                  paymentitem_form=paymentitem_form))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        paymentitem_form = PaymentItemFormSet(self.request.POST)
        if (form.is_valid() and paymentitem_form.is_valid()):
            return self.form_valid(form, paymentitem_form)
        else:
            return self.form_invalid(form, paymentitem_form)

    def form_valid(self, form, paymentitem_form):
        form.instance.created_by = self.request.user
        self.object = form.save()
        paymentitem_form.instance = self.object
        paymentitem_form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, paymentitem_form):
        """
        Called if a form is invalid. Re-renders the context data with the
        data-filled forms and errors.
        """
        return self.render_to_response(
            self.get_context_data(form=form,
                                  paymentitem_form=paymentitem_form))


def post_payment(request, pk):
    # use get_objector404
    payment = Payment.objects.get(id=pk)
    # post to dea
    payment.post()
    return redirect(payment)


def unpost_payment(request, pk):
    payment = Payment.objects.get(id=pk)
    # unpost to dea
    payment.unpost()
    return redirect(payment)
