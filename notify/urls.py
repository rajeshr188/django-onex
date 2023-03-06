from django.urls import include, path
from . import views
from .models import NoticeGroup,Notification

urlpatterns = (
    path("notify/noticegroup/",views.noticegroup_list,name = "notify_noticegroup_list"),
    path("notify/noticegroup/<int:pk>/",views.noticegroup_detail, name = "notify_noticegroup_detail"),
    path("notify/noticegroup/create/",views.noticegroup_create, name = "notify_noticegroup_create"),
)