"""
Shifts URLs
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.ShiftListView.as_view(), name='shift-list'),
    path('create/', views.ShiftCreateView.as_view(), name='shift-create'),
    path('<uuid:pk>/update/', views.ShiftUpdateView.as_view(), name='shift-update'),
    path('<uuid:pk>/delete/', views.ShiftDeleteView.as_view(), name='shift-delete'),
    path('sessions/', views.ShiftSessionListView.as_view(), name='shift-session-list'),
    path('sessions/create/', views.ShiftSessionCreateView.as_view(), name='shift-session-create'),
    path('sessions/<uuid:pk>/close/', views.ShiftSessionCloseView.as_view(), name='shift-session-close'),
    path('sessions/<uuid:pk>/reopen/', views.ShiftSessionReopenView.as_view(), name='shift-session-reopen'),
    path('current/', views.current_shift, name='current-shift'),
]
