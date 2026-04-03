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
    path('torneos/', views.TorneoListView.as_view(), name='torneo_list'),
    path('torneos/mis-torneos/', views.MisTorneosView.as_view(), name='mis_torneos'),
    path('torneos/solicitar/', views.SolicitarTorneoView.as_view(), name='solicitar_torneo'),
    path('equipos/crear/', views.EquipoCreateView.as_view(), name='crear_equipo'),
    path('equipos/mis-equipos/', views.MisEquiposView.as_view(), name='mis_equipos'),
    path('reservar/<int:reserva_id>/pagar', views.IniciarPagoWompiView.as_view(), name='iniciar_pago'),
    path('pagos/respuesta/', views.RespuestaPagoWompiView.as_view(), name='pago_respuesta'),
    path('api/webhooks/wompi/', views.WebhookWompiView.as_view(), name='wompi_webhook'),
    path('torneos/<int:pk>/', views.TorneoDetalleView.as_view(), name='torneo_detalle'),
    path('torneos/<int:pk>/generar-fixture/', views.GenerarFixtureView.as_view(), name='generar_fixture'),
    path('partidos/<int:pk>/resultado/', views.RegistrarResultadoView.as_view(), name='registrar_resultado'),
    path('analytics/', views.PanelAnalyticsView.as_view(), name='panel_analytics'),
    path('analytics/', views.PanelAnalyticsView.as_view(), name='panel_analytics'),
    path('reporte-reservas-pdf/', views.ReporteReservasPdfView.as_view(), name='reporte_reservas_pdf'),
    path('reporte-reservas-excel/', views.ReporteReservasExcelView.as_view(), name='reporte_reservas_excel'),
    path('reporte-reservas-word/', views.ReporteReservasWordView.as_view(), name='reporte_reservas_word'),
    path('reporte-torneos/', views.ReporteTorneosView.as_view(), name='reporte_torneos'),
]
