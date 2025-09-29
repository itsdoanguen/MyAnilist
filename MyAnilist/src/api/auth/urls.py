from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views.auth_views import register, login

urlpatterns = [
    # Authentication endpoints
    path('register/', register, name='auth_register'),
    path('login/', login, name='auth_login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]