from django.urls import path

from . import views

app_name = "approval"
urlpatterns = (
    # approval urls
    path("approval/", views.approval_list, name="approval_approval_list"),
    path(
        "approval/detail/<int:pk>/",
        views.approval_detail,
        name="approval_approval_detail",
    ),
    path(
        "approval/create/",
        views.approval_create,
        name="approval_approval_create",
    ),
    path(
        "approval/update/<int:pk>/",
        views.approval_update,
        name="approval_approval_update",
    ),
    path(
        "approval/delete/<int:pk>/",
        views.approval_delete,
        name="approval_approval_delete",
    ),
    path("approval/post/<int:pk>/", views.post_approval, name="approval_post"),
    path("approval/unpost/<int:pk>/", views.unpost_approval, name="approval_unpost"),
)

urlpatterns += (
    path(
        "approval/<int:approval_pk>/line/create/",
        views.approvalline_create_update,
        name="approval_approvalline_create",
    ),
    path(
        "approvalline/detail/<int:pk>/",
        views.approval_line_detail,
        name="approval_approvalline_detail",
    ),
    path(
        "approval/<int:approval_pk>/line/<int:pk>/update/",
        views.approvalline_create_update,
        name="approval_approvalline_update",
    ),
    path(
        "approvalline/<int:pk>/delete/",
        views.approvalline_delete,
        name="approval_approvalline_delete",
    ),
)

urlpatterns += (
    path(
        "approval/convert_sale/<int:pk>/",
        views.convert_sales,
        name="approval_convert_sale",
    ),
)

urlpatterns += (
    path(
        "return/",
        views.return_list,
        name="approval_return_list",
    ),
    path(
        "return/create/",
        views.return_create,
        name="approval_return_create",
    ),
    path(
        "return/update/<int:pk>/",
        views.return_update,
        name="approval_return_update",
    ),
    path(
        "return/delete/<int:pk>/",
        views.return_delete,
        name="approval_return_delete",
    ),
)

urlpatterns += (
    path(
        "returnitem/create/",
        views.returnitem_create,
        name="approval_returnitem_create",
    ),
    path(
        "returnitem/update/<int:pk>/",
        views.returnitem_update,
        name="approval_returnitem_update",
    ),
    path(
        "returnitem/delete/<int:pk>/",
        views.returnitem_delete,
        name="approval_returnitem_delete",
    ),
)
