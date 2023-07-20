from django.urls import include, path
from django.views.generic.dates import ArchiveIndexView
from rest_framework import routers

from . import api, views
from .models import Loan

router = routers.DefaultRouter()
router.register(r"license", api.LicenseViewSet)
router.register(r"loan", api.LoanViewSet)
router.register(r"release", api.ReleaseViewSet)

app_name = "girvi"

urlpatterns = (
    # urls for Django Rest Framework API
    path("api/v1/", include(router.urls)),
)

urlpatterns += (
    path("", views.home, name="girvi-home"),
    path("multirelease/", views.multirelease, name="girvi-multirelease"),
    path("deletemultiple/", views.deleteLoan, name="girvi_loan_deletemultiple"),
    path("girvi/check/", views.check_girvi, name="check_girvi"),
    path("girvi/bulk_release/", views.bulk_release, name="bulk_release"),
    path(
        "girvi/series/<int:pk>/activate",
        views.activate_series,
        name="girvi_activate_series",
    ),
    path(
        "girvi/series/next-loanid/", views.next_loanid, name="girvi_series_next_loanid"
    ),
    # Example: /2012/week/23/
    path("girvi/notice/", views.notice, name="notice"),
    path("girvi/outdatedloans/notify/", views.notify_print, name="girvi_create_notice"),
)

urlpatterns += (
    path(
        "loan_archive/",
        ArchiveIndexView.as_view(model=Loan, date_field="created"),
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
    # Example: /2012/week/23/
    path(
        "<int:year>/week/<int:week>/",
        views.LoanWeekArchiveView.as_view(),
        name="archive_week",
    ),
)

urlpatterns += (
    # urls for License
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
)

urlpatterns += (
    # urls for Loan
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
    path("girvi/loan/detail/<int:pk>/d", views.generate_duplicate, name="duplicate"),
    path(
        "girvi/loan/update/<int:id>/",
        # views.LoanUpdateView.as_view(),
        views.loan_update,
        name="girvi_loan_update",
    ),
    path(
        "girvi/loan/<int:pk>/delete/",
        views.LoanDeleteView.as_view(),
        name="girvi_loan_delete",
    ),
    path(
        "girvi/loan/take_physicalstock/",
        views.physical_stock,
        name="girvi_physicalstock_add",
    ),
    path(
        "girvi/loan/physicalstock/",
        views.physical_list,
        name="girvi_physicalstock_list",
    ),
)

urlpatterns += (
    # urls for loanitem
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

urlpatterns += (
    # urls for Adjustment
    path(
        "girvi/adjustment/",
        views.AdjustmentListView.as_view(),
        name="girvi_adjustment_list",
    ),
    path(
        "girvi/adjustment/create/",
        views.AdjustmentCreateView.as_view(),
        name="girvi_adjustment_create",
    ),
    path(
        "girvi/adjustment/<int:pk>/create/",
        views.AdjustmentCreateView.as_view(),
        name="girvi_adjustment_create",
    ),
    path(
        "girvi/adjustment/update/<int:pk>/",
        views.AdjustmentUpdateView.as_view(),
        name="girvi_adjustment_update",
    ),
    path(
        "girvi/adjustment/<int:pk>/delete",
        views.AdjustmentDeleteView.as_view(),
        name="girvi_adjustment_delete",
    ),
)

urlpatterns += (
    # urls for Release
    path("girvi/release/", views.ReleaseListView.as_view(), name="girvi_release_list"),
    path(
        "girvi/release/create/",
        views.ReleaseCreateView.as_view(),
        name="girvi_release_create",
    ),
    path(
        "girvi/release/<int:pk>/create/",
        views.ReleaseCreateView.as_view(),
        name="girvi_release_create",
    ),
    path(
        "girvi/release/detail/<int:pk>/",
        views.ReleaseDetailView.as_view(),
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
)
