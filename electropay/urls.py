"""
Main URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.views.generic import TemplateView
urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', TemplateView.as_view(template_name='dashboard/index.html'), name='home'),
    # path('dashboard/', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
path('', include('dashboard.urls')),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/accounts/', include('accounts.urls')),
    path('api/branches/', include('branches.urls')),
    path('api/wallets/', include('wallets.urls')),
    path('api/transactions/', include('transactions.urls')),
    path('api/shifts/', include('shifts.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
