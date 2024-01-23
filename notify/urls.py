from django.urls import include, path

from . import views
from .models import NoticeGroup, Notification

urlpatterns = (
    # paths for NoticeGroup
    path("noticegroup/", views.noticegroup_list, name="notify_noticegroup_list"),
    path(
        "noticegroup/<int:pk>/",
        views.noticegroup_detail,
        name="notify_noticegroup_detail",
    ),
    path(
        "noticegroup/create/",
        views.noticegroup_create,
        name="notify_noticegroup_create",
    ),
    path(
        "noticegroup/<int:pk>/delete/",
        views.noticegroup_delete,
        name="notify_noticegroup_delete",
    ),
    # paths for Notification
    path("notification/", views.notification_list, name="notify_notification_list"),
    path(
        "notification/<int:pk>/",
        views.notification_detail,
        name="notify_notification_detail",
    ),
    path(
        "notification/create/",
        views.notification_create,
        name="notify_notification_create",
    ),
    # path to print group/Notifications
    path(
        "noticegroup/<int:pk>/print",
        views.noticegroup_print,
        name="notify_noticegroup_print",
    ),
    path(
        "notification/<int:pk>/print",
        views.notification_print,
        name="notify_notification_print",
    ),
    # path to delete a notification
    path(
        "notification/<int:pk>/delete/",
        views.notification_delete,
        name="notify_notification_delete",
    ),
)
