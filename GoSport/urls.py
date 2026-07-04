"""
URL configuration for GoSport project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from core.views import DashboardView, AdminAnalyticsView
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render

def custom_page_not_found_view(request, exception):
    return render(request, "404.html", status=404)

handler404 = 'GoSport.urls.custom_page_not_found_view'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('negocio/', include('negocio.urls')),
    path('', DashboardView.as_view(), name='dashboard'),
    path('global-analytics/', AdminAnalyticsView.as_view(), name='admin_analytics'),
    path('canchas/', include('canchas.urls')),
    path('usuarios/', include('usuarios.urls')),
]

# django_browser_reload solo en desarrollo
if settings.DEBUG:
    urlpatterns += [path("__reload__/", include("django_browser_reload.urls"))]

# Servir media files en desarrollo local (en producción Cloudinary los sirve)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
