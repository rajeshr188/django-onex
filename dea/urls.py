from django.urls import path
from . import views
urlpatterns = [
    path('', views.home, name='dea_home'),

    path('accounts/', views.AccountListView.as_view(), name="dea_account_list"),
    path('account/<int:pk>/', views.AccountDetailView.as_view(),
         name="dea_account_detail"),
    path('account/add/', views.AccountCreateView.as_view(),
         name='dea_account_create'),
    path('account/<int:pk>/set-ob/', views.set_acc_ob, name='dea_account_setob'),
    path('account/accountstatement/create/',
         views.AccountStatementCreateView, name='dea_accountstatement_create'),

    path('ledger/<int:pk>/', views.LedgerDetailView.as_view(),
         name="dea_ledger_detail"),
    path('ledger/add/', views.LedgerCreateView.as_view(),
         name='dea_ledger_create'),
    path('ledger/<int:pk>/set-ob/', views.set_ledger_ob, name='dea_ledger_setob'),
    path('ledger/ledgerstatement/create/',
         views.LedgerStatementCreateView, name='dea_ledgerstatement_create'),
    path('accounts/<int:pk>/mock_pledge_loan',
         views.mock_pledge_loan, name="dea_pledge_loan"),
    path('accounts/<int:pk>/mock_repay_loan/',
         views.mock_repay_loan, name='dea_repay_loan'),

]
