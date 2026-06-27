# usuarios/urls.py
from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('registro/', views.registro, name='registro'),
    path('perfil/', views.PerfilUpdateView.as_view(), name='perfil'),
    path('perfil/password/', views.CustomPasswordChangeView.as_view(), name='cambiar_password'),
    path('reporte/', views.ReporteUsuariosView.as_view(), name='reporte_usuarios'),
    path('gestion/', views.AdminUserListView.as_view(), name='admin_user_list'),
    path('gestion/<int:pk>/editar/', views.AdminUserUpdateView.as_view(), name='admin_user_update'),
    path('gestion/<int:pk>/eliminar/', views.AdminUserDeleteView.as_view(), name='admin_user_delete'),
]
