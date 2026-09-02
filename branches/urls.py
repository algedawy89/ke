"""
Branches URLs
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.BranchListView.as_view(), name='branch-list'),
    path('create/', views.BranchCreateView.as_view(), name='branch-create'),
    path('<uuid:pk>/', views.BranchDetailView.as_view(), name='branch-detail'),
    path('<uuid:pk>/update/', views.BranchUpdateView.as_view(), name='branch-update'),
    path('<uuid:pk>/delete/', views.BranchDeleteView.as_view(), name='branch-delete'),
    path('<uuid:pk>/toggle-active/', views.BranchToggleActiveView.as_view(), name='branch-toggle-active'),
]
