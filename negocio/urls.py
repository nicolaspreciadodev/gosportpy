from django.urls import path
from .views import CrearReservaView, FacturaDetalleView

app_name = 'negocio'

urlpatterns = [
    path('reservar/<int:cancha_id>/', CrearReservaView.as_view(), name='crear_reserva'),
    path('factura/<int:factura_id>/', FacturaDetalleView.as_view(), name='factura_detalle'),
]
