from django.urls import include, path
from . import views
from .model import NoticeGroup,Notification
urlpatterns = (
    path("notify/noticegroup/",views.noticegroup_list,name = "girvi_noticegroup_list"),
    path("notify/noticegroup/<int:pk>/",views.noticegroup_detail, name = "girvi_noticegroup_detail"),
    path("notify/noticegroup/create/",views.noticegroup_create, name = "girvi_noticegroup_create"),
)