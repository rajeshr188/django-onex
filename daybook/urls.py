from django.urls import path, include
from . import views
urlpatterns = (
    # urls for Customer
    path('daybook/',views.daybook,name='daybook'),

)
