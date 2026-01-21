"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Connexion / Déconnexion
    path('login/', auth_views.LoginView.as_view(template_name='gestion/registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),    
    # Inclure les urls de l'application gestion
    path('', include('gestion.urls')),
    
    
    
    # 1. Page pour demander la réinitialisation (saisir l'email)
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='gestion/auth/password_reset.html'), name='password_reset'),
    
    # 2. Confirmation que l'email a été envoyé
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='gestion/auth/password_reset_done.html'), name='password_reset_done'),
    
    # 3. Le lien spécial reçu par email (sécurisé)
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='gestion/auth/password_reset_confirm.html'), name='password_reset_confirm'),
    
    # 4. Confirmation que le mot de passe est changé
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='gestion/auth/password_reset_complete.html'), name='password_reset_complete'),
]
