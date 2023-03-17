from django.contrib.auth.mixins import LoginRequiredMixin

from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import AllotmentForm, ChitForm, CollectionForm, ContactForm
from .models import Allotment, Chit, Collection, Contact


class ContactListView(LoginRequiredMixin, ListView):
    model = Contact


class ContactCreateView(LoginRequiredMixin, CreateView):
    model = Contact
    form_class = ContactForm


class ContactDetailView(LoginRequiredMixin, DetailView):
    model = Contact


class ContactUpdateView(LoginRequiredMixin, UpdateView):
    model = Contact
    form_class = ContactForm


class ChitListView(LoginRequiredMixin, ListView):
    model = Chit


class ChitCreateView(LoginRequiredMixin, CreateView):
    model = Chit
    form_class = ChitForm


class ChitDetailView(LoginRequiredMixin, DetailView):
    model = Chit


class ChitUpdateView(LoginRequiredMixin, UpdateView):
    model = Chit
    form_class = ChitForm


class CollectionListView(LoginRequiredMixin, ListView):
    model = Collection


class CollectionCreateView(LoginRequiredMixin, CreateView):
    model = Collection
    form_class = CollectionForm

    def get_form(self, form_class=None, *args, **kwargs):
        self.pk = self.kwargs["pk"]
        form = super(CollectionCreateView, self).get_form(form_class)
        all = Allotment.objects.get(id=self.pk)
        form.fields["allotment"].queryset = Allotment.objects.filter(id=self.pk)
        form.fields["allotment"].initial = all
        form.fields["amount"].initial = all.installment
        form.fields["member"].queryset = all.chit.members
        return form


class CollectionDetailView(LoginRequiredMixin, DetailView):
    model = Collection


class CollectionUpdateView(LoginRequiredMixin, UpdateView):
    model = Collection
    form_class = CollectionForm


class AllotmentListView(LoginRequiredMixin, ListView):
    model = Allotment


class AllotmentCreateView(LoginRequiredMixin, CreateView):
    model = Allotment
    form_class = AllotmentForm
    extra_context = {}

    def get_context_data(self, **kwargs):
        context = super(AllotmentCreateView, self).get_context_data(**kwargs)
        c = Chit.objects.get(id=self.kwargs["pk"])
        context["chitamount"] = c.amount
        context["chitcommission"] = c.amount - c.get_commission_amount()
        context["remaining"] = c.get_noofallotments_rem()
        context["trialamount"] = (c.amount - c.get_commission_amount()) - (
            c.amount - c.get_commission_amount()
        ) * 10 / 100
        context.update(self.extra_context)
        return context

    def get_form(self, form_class=None, *args, **kwargs):
        self.ct = self.kwargs["pk"]
        chi = Chit.objects.get(id=self.ct)

        form = super(AllotmentCreateView, self).get_form(form_class)

        form.fields["chit"].queryset = Chit.objects.filter(id=self.ct)
        form.fields["chit"].initial = chi

        form.fields["to_member"].queryset = chi.members.filter(allotment__isnull=True)
        return form

    def form_valid(self, form):
        form.instance.name = (
            form.instance.chit.name
            + " /"
            + str(form.instance.chit.allotment_set.count() + 1)
        )
        form.instance.installment = (
            form.instance.amount + form.instance.chit.get_commission_amount()
        ) / form.instance.chit.members.count()
        return super().form_valid(form)


class AllotmentDetailView(LoginRequiredMixin, DetailView):
    model = Allotment


class AllotmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Allotment
    form_class = AllotmentForm

    def form_valid(self, form):
        form.instance.name = (
            form.instance.chit.name
            + " /"
            + str(form.instance.chit.allotment_set.count())
        )
        return super().form_valid(form)
