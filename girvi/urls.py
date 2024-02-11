from django.urls import include, path
from django.views.generic.dates import ArchiveIndexView

from . import views
from .models import Loan

app_name = "girvi"

urlpatterns = (
    # create a path to create notification view
    path("girvi/loan/<int:pk>/notify/", views.create_loan_notification, name="girvi_loan_notice"),
    path("deletemultiple/", views.deleteLoan, name="girvi_loan_deletemultiple"),
    path("girvi/check/", views.check_girvi, name="check_girvi"),
    path("girvi/check/<int:pk>/", views.check_girvi, name="check_girvi_statement"),
    path("girvi/statement/add/", views.statement_create, name="statement_add"),
    path(
        "girvi/loan/get-interestrate/",
        views.get_interestrate,
        name="girvi_get_interestrate",
    ),
    # Example: /2012/week/23/
    path("girvi/notice/", views.notice, name="notice"),
    path("girvi/outdatedloans/notify/", views.notify_print, name="girvi_create_notice"),
)

# urls for archive views
urlpatterns += (
    path(
        "loan_archive/",
        ArchiveIndexView.as_view(model=Loan, date_field="loan_date"),
        name="loan_archive",
    ),
    path("<int:year>/", views.LoanYearArchiveView.as_view(), name="loan_year_archive"),
    # Example: /2012/08/
    path(
        "<int:year>/<int:month>/",
        views.LoanMonthArchiveView.as_view(month_format="%m"),
        name="archive_month_numeric",
    ),
    # Example: /2012/aug/
    path(
        "<int:year>/<str:month>/",
        views.LoanMonthArchiveView.as_view(),
        name="archive_month",
    ),
    path(
        "<int:year>/<str:month>/<int:day>/",
        views.LoanDayArchiveView.as_view(),
        name="archive_day",
    ),
    # Example: /2012/week/23/
    path(
        "<int:year>/week/<int:week>/",
        views.LoanWeekArchiveView.as_view(),
        name="archive_week",
    ),
    path("today/", views.LoanTodayArchiveView.as_view(), name="archive_today"),
)

# urls for License
urlpatterns += (
    path("girvi/license/", views.license_list, name="girvi_license_list"),
    path(
        "girvi/license/create/",
        views.LicenseCreateView.as_view(),
        name="girvi_license_create",
    ),
    path(
        "girvi/license/detail/<int:pk>/",
        views.LicenseDetailView.as_view(),
        name="girvi_license_detail",
    ),
    path(
        "girvi/license/update/<int:pk>/",
        views.LicenseUpdateView.as_view(),
        name="girvi_license_update",
    ),
    path(
        "girvi/license/<int:pk>/delete/",
        views.LicenseDeleteView.as_view(),
        name="girvi_license_delete",
    ),
    path(
        "license/series/create/",
        views.SeriesCreateView.as_view(),
        name="girvi_series_create",
    ),
    path(
        "license/series/detail/<int:id>/",
        views.SeriesDetailView.as_view(),
        name="girvi_series_detail",
    ),
)

# urls for Loan
urlpatterns += (
    path("girvi/loan/", views.loan_list, name="girvi_loan_list"),
    path("girvi/loan/renew/<int:pk>/", views.loan_renew, name="girvi_loan_renew"),
    path("girvi/loan/create/", views.create_loan, name="girvi_loan_create"),
    path(
        "girvi/loan/create/<int:pk>",
        views.create_loan,
        name="girvi_loan_create",
    ),
    path("girvi/loan/detail/<int:pk>/", views.loan_detail, name="girvi_loan_detail"),
    path("girvi/loan/detail/<int:pk>/pdf", views.print_loan, name="loan_pdf"),
    path("girvi/loan/detail/<int:pk>/o", views.generate_original, name="original"),
    path(
        "girvi/loan/update/<int:id>/",
        views.loan_update,
        name="girvi_loan_update",
    ),
    path(
        "girvi/loan/<int:pk>/delete/",
        views.loan_delete,
        name="girvi_loan_delete",
    ),
)

# urls for loanitem
urlpatterns += (
    path(
        "loan/<int:parent_id>/item/create",
        views.loan_item_update_hx_view,
        name="girvi_loanitem_create",
    ),
    path(
        "loan/<int:parent_id>/item/<int:id>/",
        views.loan_item_update_hx_view,
        name="hx-loanitem-detail",
    ),
    path(
        "loan/item/<int:pk>/detail", views.loanitem_detail, name="girvi_loanitem_detail"
    ),
    path(
        "loan/<int:parent_id>/item/<int:id>/delete/",
        views.loanitem_delete,
        name="girvi_loanitem_delete",
    ),
)

# urls for LoanPayment
urlpatterns += (
    path(
        "girvi/loanpayment/",
        views.loan_payment_list_view,
        name="girvi_loanpayment_list",
    ),
    path(
        "girvi/loanpayment/create/",
        views.loan_payment_create_view,
        name="girvi_loanpayment_create",
    ),
    path(
        "girvi/loanpayment/<int:pk>/create/",
        views.loan_payment_create_view,
        name="girvi_loanpayment_create",
    ),
    path(
        "girvi/loanpayment/update/<int:pk>/",
        views.loan_payment_update_view,
        name="girvi_loanpayment_update",
    ),
    path(
        "girvi/loanpayment/<int:pk>/delete",
        views.loan_payment_delete_view,
        name="girvi_loanpayment_delete",
    ),
)

# urls for series
urlpatterns += (
    path("girvi/series/", views.series_list, name="girvi_series_list"),
    path(
        "girvi/series/create/",
        views.series_new,
        name="girvi_series_create",
    ),
    path(
        "girvi/series/detail/<int:pk>/",
        views.series_detail,
        name="girvi_series_detail",
    ),
    path(
        "girvi/series/update/<int:pk>/",
        views.series_edit,
        name="girvi_series_update",
    ),
    path(
        "girvi/series/<int:pk>/delete/",
        views.series_delete,
        name="girvi_series_delete",
    ),
    path(
        "girvi/series/<int:pk>/activate",
        views.activate_series,
        name="girvi_activate_series",
    ),
    path(
        "girvi/series/next-loanid/", views.next_loanid, name="girvi_series_next_loanid"
    ),
)

# urls for Release
urlpatterns += (
    path("girvi/release/", views.release_list, name="girvi_release_list"),
    path(
        "girvi/release/create/",
        views.release_create,
        name="girvi_release_create",
    ),
    path(
        "girvi/release/<int:pk>/create/",
        views.release_create,
        name="girvi_release_create",
    ),
    path(
        "girvi/release/detail/<int:pk>/",
        views.release_detail,
        name="girvi_release_detail",
    ),
    path(
        "girvi/release/update/<int:pk>/",
        views.ReleaseUpdateView.as_view(),
        name="girvi_release_update",
    ),
    path(
        "girvi/release/<int:pk>/delete",
        views.ReleaseDeleteView.as_view(),
        name="girvi_release_delete",
    ),
    path("girvi/bulk_release/", views.bulk_release, name="bulk_release"),
    path(
        "girvi/bulk_release/details/",
        views.get_release_details,
        name="bulk_release_details",
    ),
)
