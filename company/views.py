from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.views.generic.base import View
from company.forms import CompanyForm,MembershipForm
from company.models import Company,CompanyOwner,Membership
from django.shortcuts import render
from django.views.generic import ListView,DetailView,CreateView, DeleteView
from django.urls import reverse_lazy
from django.db import transaction
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from tenant_schemas.utils import remove_www
from django.contrib.auth.mixins import UserPassesTestMixin
import logging

logger = logging.getLogger(__name__)
class MemberOnly(UserPassesTestMixin, View):

    def test_func(self):
        return Membership.objects.filter(user = self.request.user,
        company = self.get_object()).exists()


class AdminOnly(UserPassesTestMixin, View):

    def test_func(self):
        return Membership.objects.filter(user=self.request.user,
             company=self.get_object(),role='admin').exists()

# Create your views here.

class CompanyOwnerListView(LoginRequiredMixin,ListView):
    model = CompanyOwner

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

class CompanyCreateView(SuccessMessageMixin, LoginRequiredMixin,CreateView):
    model = Company
    form_class = CompanyForm
    success_url = reverse_lazy('membership_list')
    success_message = 'Company Created Successfully'

    @transaction.atomic()
    def form_valid(self, form):
        # form.instance.created_by = self.request.user
        schema_name = form.instance.name.lower() 
        form.instance.schema_name = schema_name
        hostname = remove_www(self.request.get_host().split(":")[0]).lower()
        form.instance.domain_url = schema_name + hostname
        response = super(CompanyCreateView, self).form_valid(form)
        # do something with self.object
        owner = CompanyOwner.objects.create(company = self.object,user = self.request.user)
        member = Membership.objects.create(company = self.object,user = self.request.user,role='admin')
        return response

# only members/admin shall pass
class CompanyDetailView(LoginRequiredMixin,MemberOnly,DetailView):
    model = Company

# only admin shall pass
class CompanyDeleteView(LoginRequiredMixin,AdminOnly,DeleteView):
    model = Company
    success_url = reverse_lazy('company_owned_list')

class MembershipListView(LoginRequiredMixin,ListView):
    model = Membership

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

@login_required
def change_workspace(request,pk):
    company = Company.objects.get(id=pk)
    request.user.workspace = company
    request.user.save()
    return redirect('/')

@login_required
def clear_workspace(request):
    request.user.workspace = None
    request.user.save()
    return redirect('/')

# only admin shall pass
@login_required
def add_member(request):
    user = request.user
    if request.method =='POST':
        form = MembershipForm(user,request.POST)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.INFO, 'Member added successfully.')
            redirect('company_owned_list')
    else:
        form = MembershipForm(user)

    return render(request,'company/add_member.html',{'form':form})
