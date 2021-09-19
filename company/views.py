from django.contrib.messages.views import SuccessMessageMixin
from company.forms import CompanyForm,MembershipForm
from company.models import Company,CompanyOwner,Membership
from django.shortcuts import render
from django.views.generic import ListView,DetailView,CreateView, DeleteView
from django.urls import reverse_lazy
from django.db import transaction
from django.shortcuts import redirect

# Create your views here.
class CompanyOwnerListView(ListView):
    model = CompanyOwner

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

class CompanyCreateView(SuccessMessageMixin,CreateView):
    model = Company
    form_class = CompanyForm
    success_url = reverse_lazy('membership_list')
    success_message = 'Company Created Successfully'

    @transaction.atomic()
    def form_valid(self, form):
        # form.instance.created_by = self.request.user
        form.instance.schema_name = form.instance.name
        form.instance.domain_url = form.instance.name
        response = super(CompanyCreateView, self).form_valid(form)
        # do something with self.object
        owner = CompanyOwner.objects.create(company = self.object,user = self.request.user)
        member = Membership.objects.create(company = self.object,user = self.request.user,role='admin')
        return response

class CompanyDetailView(DetailView):
    model = Company

class CompanyDeleteView(DeleteView):
    model = Company
    success_url = reverse_lazy('company_owned_list')

class MembershipListView(ListView):
    model = Membership

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

def change_workspace(request,pk):
    company = Company.objects.get(id=pk)
    request.user.workspace = company
    request.user.save()
    return redirect('/')

def add_member(request):
    user = request.user
    if request.method =='POST':
        form = MembershipForm(user,request.POST)
        if form.is_valid():
            form.save()
            redirect('company_owned_list')
    else:
        form = MembershipForm(user)

    return render(request,'company/add_member.html',{'form':form})