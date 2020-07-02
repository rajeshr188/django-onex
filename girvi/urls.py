from django.urls import path, include
from django.views.generic.dates import ArchiveIndexView
from .models import Loan
from rest_framework import routers
from django_filters.views import FilterView
from . import api
from . import views

router = routers.DefaultRouter()
router.register(r'license', api.LicenseViewSet)
router.register(r'loan', api.LoanViewSet)
router.register(r'release', api.ReleaseViewSet)


urlpatterns = (
    # urls for Django Rest Framework API
    path('api/v1/', include(router.urls)),
)
urlpatterns +=(
    path('',views.home,name='girvi-home'),
)
urlpatterns +=(
    path('multirelease/',views.multirelease,name='girvi-multirelease'),
)
urlpatterns +=(
    path('loan_archive/',
         ArchiveIndexView.as_view(model=Loan, date_field="created"),
         name="loan_archive"),
)
urlpatterns +=(
    path('<int:year>/',
         views.LoanYearArchiveView.as_view(),
         name="loan_year_archive"),
)
urlpatterns += (
    # Example: /2012/08/
    path('<int:year>/<int:month>/',
         views.LoanMonthArchiveView.as_view(month_format='%m'),
         name="archive_month_numeric"),
    # Example: /2012/aug/
    path('<int:year>/<str:month>/',
         views.LoanMonthArchiveView.as_view(),
         name="archive_month"),
)
urlpatterns += (
    # Example: /2012/week/23/
    path('<int:year>/week/<int:week>/',
         views.LoanWeekArchiveView.as_view(),
         name="archive_week"),
)
urlpatterns += (
    # urls for License
    path('girvi/license/', views.LicenseListView.as_view(), name='girvi_license_list'),
    path('girvi/license/create/', views.LicenseCreateView.as_view(), name='girvi_license_create'),
    path('girvi/license/detail/<int:pk>/', views.LicenseDetailView.as_view(), name='girvi_license_detail'),
    path('girvi/license/update/<int:pk>/', views.LicenseUpdateView.as_view(), name='girvi_license_update'),
    path('girvi/license/<int:pk>/delete/',views.LicenseDeleteView.as_view(), name='girvi_license_delete'),
)

urlpatterns += (
    # urls for Loan
    path('girvi/loan/', views.LoanListView.as_view(), name='girvi_loan_list'),
    path('girvi/loan/manage/',views.manage_loans,name='manage_loans'),
    path('girvi/loan/renew/<int:pk>/',views.loan_renew, name = 'girvi_loan_renew'),
    path('girvi/loan/create/', views.LoanCreateView.as_view(), name='girvi_loan_create'),
    path('girvi/loan/<int:pk>/create/', views.LoanCreateView.as_view(), name='girvi_loan_create'),
    path('girvi/loan/detail/<int:pk>/', views.LoanDetailView.as_view(), name='girvi_loan_detail'),
    path('girvi/loan/detail/<int:pk>/pdf', views.print_loanpledge, name='loan_pdf'),
    path('girvi/loan/update/<int:pk>/', views.LoanUpdateView.as_view(), name='girvi_loan_update'),
    path('girvi/loan/<int:pk>/delete/',views.LoanDeleteView.as_view(),name='girvi_loan_delete'),
)
urlpatterns += (
    # urls for Adjustment
    path('girvi/adjustment/', views.AdjustmentListView.as_view(), name='girvi_adjustment_list'),
    path('girvi/adjustment/create/', views.AdjustmentCreateView.as_view(), name='girvi_adjustment_create'),
    path('girvi/adjustment/<int:pk>/create/', views.AdjustmentCreateView.as_view(), name='girvi_adjustment_create'),
    path('girvi/adjustment/update/<int:pk>/', views.AdjustmentUpdateView.as_view(), name='girvi_adjustment_update'),
    path('girvi/adjustment/<int:pk>/delete',views.AdjustmentDeleteView.as_view(),name='girvi_adjustment_delete'),
)

urlpatterns += (
    # urls for Release
    path('girvi/release/', views.ReleaseListView.as_view(), name='girvi_release_list'),
    path('girvi/release/create/', views.ReleaseCreateView.as_view(), name='girvi_release_create'),
    path('girvi/release/<int:pk>/create/', views.ReleaseCreateView.as_view(), name='girvi_release_create'),
    path('girvi/release/detail/<int:pk>/', views.ReleaseDetailView.as_view(), name='girvi_release_detail'),
    path('girvi/release/update/<int:pk>/', views.ReleaseUpdateView.as_view(), name='girvi_release_update'),
    path('girvi/release/<int:pk>/delete',views.ReleaseDeleteView.as_view(),name='girvi_release_delete'),
)
urlpatterns += (
    # Example: /2012/week/23/
    path('girvi/notice/',
         views.notice,
         name="notice"),

)
