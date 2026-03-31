# usuarios/urls.py
from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('registro/', views.registro, name='registro'),
    path('perfil/', views.PerfilUpdateView.as_view(), name='perfil'),
    path('perfil/password/', views.CustomPasswordChangeView.as_view(), name='cambiar_password'),
    path('reporte/', views.ReporteUsuariosView.as_view(), name='reporte_usuarios'),
]
