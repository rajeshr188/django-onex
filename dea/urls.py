from django.urls import path
from . import views
urlpatterns = [
    path('', views.home, name='dea_home'),
    path('daybook/',views.daybook, name='dea_daybook'),
    path('account/', views.AccountListView.as_view(),
          name="dea_account_list"),
    path('account/<int:pk>/', views.AccountDetailView.as_view(),
          name="dea_account_detail"),
    path('account/add/', views.AccountCreateView.as_view(),
          name='dea_account_create'),
    path('account/<int:pk>/set-ob/', views.set_acc_ob,
          name='dea_account_setob'),
    path('account/accountstatement/create/',
         views.AccountStatementCreateView, 
         name = 'dea_accountstatement_create'),
    path('account/<int:pk>/audit/',views.audit_acc, 
          name = 'dea_account_audit'), 

    path('ledger/audit/',views.audit_ledger,\
         name = 'dea_ledger_audit'), 
    path('ledger/',views.LedgerListView.as_view(),\
         name = 'dea_ledger_list'),
    path('ledger/<int:pk>/', views.LedgerDetailView.as_view(),
         name="dea_ledger_detail"),
    path('ledger/add/', views.LedgerCreateView.as_view(),
         name='dea_ledger_create'),
    path('ledger/<int:pk>/set-ob/', views.set_ledger_ob,\
         name='dea_ledger_setob'),
    path('ledger/ledgerstatement/create/',
         views.LedgerStatementCreateView, 
         name='dea_ledgerstatement_create'),

         
     path('journals/',views.JournalListView.as_view(),
     name='dea_journals_list'),

]
