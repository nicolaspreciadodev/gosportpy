from django.urls import path
from negocio import views

app_name = 'negocio'

urlpatterns = [
    path('reservar/<int:cancha_id>/', views.CrearReservaView.as_view(), name='crear_reserva'),
    path('facturas/<int:factura_id>/', views.FacturaDetalleView.as_view(), name='factura_detalle'),
    path('reservar/<int:reserva_id>/cancelar', views.CancelarReservaView.as_view(), name='cancelar_reserva'),
    path('inscribir-equipo/<int:torneo_id>/', views.InscribirEquipoView.as_view(), name='inscribir_torneo'),
    path('aprobar-torneo/<int:torneo_id>/', views.AprobarTorneoView.as_view(), name='aprobar_torneo'),
    path('mis-reservas/', views.PanelReservasView.as_view(), name='panel_reservas'),
    path('reservar/<int:reserva_id>/pagar', views.SimularPagoView.as_view(), name='simular_pago'),
    path('torneos/<int:pk>/', views.TorneoDetalleView.as_view(), name='torneo_detalle'),
    path('torneos/<int:pk>/generar-fixture/', views.GenerarFixtureView.as_view(), name='generar_fixture'),
    path('partidos/<int:pk>/resultado/', views.RegistrarResultadoView.as_view(), name='registrar_resultado'),
]
