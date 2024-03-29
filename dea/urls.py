from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="dea_home"),
    path("dea/gl/", views.generalledger, name="dea_general_ledger"),
    path("daybook/", views.daybook, name="dea_daybook"),
    path("account/", views.AccountListView.as_view(), name="dea_account_list"),
    # path(
    #     "account/<int:pk>/",
    #     views.AccountDetailView.as_view(),
    #     name="dea_account_detail",
    # ),
    path("account/<int:pk>/", views.account_detail, name="dea_account_detail"),
    path("account/add/", views.AccountCreateView.as_view(), name="dea_account_create"),
    path("account/<int:pk>/set-ob/", views.set_acc_ob, name="dea_account_setob"),
    path(
        "account/accountstatement/create/",
        views.AccountStatementCreateView.as_view(),
        name="dea_accountstatement_create",
    ),
    path(
        "account/accountstatement/",
        views.AccountStatementListView.as_view(),
        name="dea_accountstatement_list",
    ),
    path(
        "account/accountstatement/<int:pk>/delete",
        views.AccountStatementDeleteView.as_view(),
        name="dea_accountstatement_delete",
    ),
    path("account/<int:pk>/audit/", views.audit_acc, name="dea_account_audit"),
    path("ledger/audit/", views.audit_ledger, name="dea_ledger_audit"),
    path("ledger/", views.LedgerListView.as_view(), name="dea_ledger_list"),
    path(
        "ledger/<int:pk>/", views.LedgerDetailView.as_view(), name="dea_ledger_detail"
    ),
    path("ledger/add/", views.LedgerCreateView.as_view(), name="dea_ledger_create"),
    path("ledger/<int:pk>/set-ob/", views.set_ledger_ob, name="dea_ledger_setob"),
    path(
        "ledger/ledgerstatement/create/",
        views.LedgerStatementCreateView.as_view(),
        name="dea_ledgerstatement_create",
    ),
    path(
        "ledger/statement/",
        views.LedgerStatementListView.as_view(),
        name="dea_ledgerstatement_list",
    ),
    path(
        "ledger/transaction/",
        views.LedgerTransactionListView.as_view(),
        name="dea_ledgertransaction_list",
    ),
    path(
        "journal_entries/",
        views.JournalEntryListView.as_view(),
        name="dea_journal_entries_list",
    ),
    path(
        "journal_entry/<int:pk>/detail",
        views.JournalEntryDetailView.as_view(),
        name="dea_journal_entry_detail",
    ),
    path(
        "journal_entry/<int:pk>/delete",
        views.JournalEntryDeleteView.as_view(),
        name="dea_journal_entry_delete",
    ),
]
