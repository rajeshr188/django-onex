from django.urls import path, include
from rest_framework import routers

from . import api
from . import views
router = routers.DefaultRouter()
router.register(r'contact', api.ContactViewSet)
router.register(r'chit', api.ChitViewSet)
router.register(r'collection', api.CollectionViewSet)
router.register(r'allotment', api.AllotmentViewSet)


urlpatterns = (
    # urls for Django Rest Framework API
    path('api/v1/', include(router.urls)),
)

urlpatterns += (
    # urls for Contact
    path('contact/', views.ContactListView.as_view(), name='contact_list'),
    path('contact/create/', views.ContactCreateView.as_view(), name='contact_create'),
    path('contact/detail/<slug:slug>/', views.ContactDetailView.as_view(), name='contact_detail'),
    path('contact/update/<slug:slug>/', views.ContactUpdateView.as_view(), name='contact_update'),
)

urlpatterns += (
    # urls for Chit
    path('chit/', views.ChitListView.as_view(), name='chit_list'),
    path('chit/create/', views.ChitCreateView.as_view(), name='chit_create'),
    path('chit/detail/<slug:slug>/', views.ChitDetailView.as_view(), name='chit_detail'),
    path('chit/update/<slug:slug>/', views.ChitUpdateView.as_view(), name='chit_update'),
)

urlpatterns += (
    # urls for Collection
    path('collection/', views.CollectionListView.as_view(), name='collection_list'),
    path('collection/create/<int:pk>/', views.CollectionCreateView.as_view(), name='collection_create'),
    path('collection/detail/<slug:slug>/', views.CollectionDetailView.as_view(), name='collection_detail'),
    path('collection/update/<slug:slug>/', views.CollectionUpdateView.as_view(), name='collection_update'),
)

urlpatterns += (
    # urls for Allotment
    path('allotment/', views.AllotmentListView.as_view(), name='allotment_list'),
    path('allotment/create/<int:pk>/', views.AllotmentCreateView.as_view(), name='allotment_create'),
    path('allotment/detail/<slug:slug>/', views.AllotmentDetailView.as_view(), name='allotment_detail'),
    path('allotment/update/<slug:slug>/', views.AllotmentUpdateView.as_view(), name='allotment_update'),
)
