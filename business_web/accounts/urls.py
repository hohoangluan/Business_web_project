from django.urls import path
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from .views import (
    register_view,
    logout_view,
    dashboard_view,
    user_list_view,
    assign_role_view,
    assign_permissions_view,
    delete_user_view,
)

urlpatterns = [
    # ---------- Public routes ----------
    path('', lambda request: redirect('login'), name='home'),
    path('register/', register_view, name='register'),
    path('login/', LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),

    # ---------- Admin routes (Master / superuser only) ----------
    path('users/', user_list_view, name='user_list'),
    path('users/<int:user_id>/role/', assign_role_view, name='assign_role'),
    path('users/<int:user_id>/permissions/', assign_permissions_view, name='assign_permissions'),
    path('users/<int:user_id>/delete/', delete_user_view, name='delete_user'),
]