from django.urls import path,include
from . import views

urlpatterns = (
# approval urls
    path('approval/',views.ApprovalListView.as_view(),
                name = 'approval_approval_list'),
    path('approval/detail/<int:pk>/',views.ApprovalDetailView.as_view(),
                name = 'approval_approval_detail'),
    path('approval/create/',views.ApprovalCreateView.as_view(),
                name ='approval_approval_create'),
    path('approval/update/<int:pk>/',views.ApprovalUpdateView.as_view(),
                name = 'approval_approval_update'),
    path('approval/delete/<int:pk>/',views.ApprovalDeleteView.as_view(),
                name = 'approval_approval_delete'),
    path('approval/post/<int:pk>/',views.post_approval,
                name = 'approval_post'),
    path('approval/unpost/<int:pk>/',views.unpost_approval,
                name='approval_unpost'),
)

urlpatterns +=(
    path('approvalline/create/',views.ApprovalLineCreateView.as_view(),
                name ='approval_approvalline_create'),
    path('approvallinereturn/',views.ApprovalLineReturnView,
                name='approval_approvallinereturn_create'),
    path('approvallinereturnlist/',views.ApprovalLineReturnListView.as_view(),
                name ='approval_approvallinereturn_list'),
    path('approvallinereturn/delete/<int:pk>/',views.ApprovalLineReturnDeleteView.as_view(),
                name = 'approval_approvallinereturn_delete'),
    path('approvallinereturn/post/<int:pk>/', views.post_approvallinereturn,
                name='approvallinereturn_post'),
    path('approvallinereturn/unpost/<int:pk>/',
         views.unpost_approvallinereturn, name='approvallinereturn_unpost'),
    path('approval/convert_sale/<int:pk>/',views.convert_sales,
                name='approval_convert_sale'),
)
