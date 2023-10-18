from django.urls import re_path, path
from rest_framework.routers import DefaultRouter
from .views import AddUserCurrencyAPIView, CurrencyDataAPIView, CurrencyHistoryAPIView

# router = DefaultRouter()
# router.register(r"assignments", AssignmentViewSet, basename="assignments")
# assignments_urlpatterns = router.urls

urlpatterns = [
    path('currency/user_currency/', AddUserCurrencyAPIView.as_view(), name='add_user_currency'),
    path('rates/', CurrencyDataAPIView.as_view(), name='currency_today_data'),
    path('currency/<int:currency_id>/analytics/',CurrencyHistoryAPIView.as_view(), name='currency_analytics')
]
