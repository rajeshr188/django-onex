from django.urls import path

from . import views

urlpatterns = (
    path("company/create/", views.CompanyCreateView.as_view(), name="company_create"),
    path(
        "company/owned/",
        views.CompanyOwnerListView.as_view(),
        name="company_owned_list",
    ),
    path(
        "company/<int:pk>/detail/",
        views.CompanyDetailView.as_view(),
        name="company_detail",
    ),
    path(
        "company/<int:pk>/delete/",
        views.CompanyDeleteView.as_view(),
        name="company_delete",
    ),
    path("membership/", views.MembershipListView.as_view(), name="membership_list"),
    path("membership/add/", views.add_member, name="company_add_member"),
    path(
        "workspace/change/<int:pk>/",
        views.change_workspace,
        name="company_change_workspace",
    ),
)
