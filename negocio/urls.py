from django.urls import path
from negocio.views import CrearReservaView, FacturaDetalleView, CancelarReservaView, InscribirEquipoView, AprobarTorneoView

app_name = 'negocio'

urlpatterns = [
    path('reservar/<int:cancha_id>/', CrearReservaView.as_view(), name='crear_reserva'),
    path('facturas/<int:factura_id>/', FacturaDetalleView.as_view(), name='factura_detalle'),
    path('reservar/<int:reserva_id>/cancelar', CancelarReservaView.as_view(), name='cancelar_reserva'),
    path('inscribir-equipo/<int:torneo_id>/', InscribirEquipoView.as_view(), name='inscribir_torneo'),
    path('aprobar-torneo/<int:torneo_id>/', AprobarTorneoView.as_view(), name='aprobar_torneo'),
]
