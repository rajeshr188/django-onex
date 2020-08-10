from django.urls import path,include
from . import views

urlpatterns = (
# approval urls
    path('approval/',views.ApprovalListView.as_view(),name = 'approval_approval_list'),
    path('approval/detail/<int:pk>/',views.ApprovalDetailView.as_view(),name = 'approval_approval_detail'),
    path('approval/create/',views.ApprovalCreateView.as_view(),name ='approval_approval_create'),
    path('approval/update/<int:pk>/',views.ApprovalUpdateView.as_view(),name = 'approval_approval_update'),
    path('approval/delete/<int:pk>/',views.ApprovalDeleteView.as_view(),name = 'approval_approval_delete'),
)

urlpatterns +=(
    path('approvalline/create/',views.ApprovalLineCreateView.as_view(),name ='approval_approvalline_create'),
    path('approvallinereturn/',views.ApprovalLineReturnView,name='approvallinereturn'),
    path('approvallinereturnlist/',views.ApprovalLineReturnListView.as_view(),name ='approval_approvallinereturn_list'),
    path('approvallinereturn/delete/<int:pk>/',views.ApprovalLineReturnDeleteView.as_view(),name = 'approval_approvallinereturn_delete'),
#approvalreturn urls
)

urlpatterns +=(
    path('approvalreturn/',views.ApprovalReturnListView.as_view(),name = 'approval_approvalreturn_list'),
    path('approvalreturn/detail/<int:pk>/',views.ApprovalReturnDetailView.as_view(),name = 'approval_approvalreturn_detail'),
    path('approvalreturn/create/',views.ApprovalReturnCreateView.as_view(),name ='approval_approvalreturn_create'),
    path('approvalreturn/update/<int:pk>/',views.ApprovalReturnUpdateView.as_view(),name = 'approval_approvalreturn_update'),
    path('approvalreturn/delete/<int:pk>/',views.ApprovalReturnDeleteView.as_view(),name = 'approval_approvalreturn_delete'),
#approvalreturn urls
)

urlpatterns +=(
    path('approvalreturnline/create/',views.ApprovalReturnLineCreateView.as_view(),name ='approval_approvalRtuenline_create'),
#approvalreturn urls
)
