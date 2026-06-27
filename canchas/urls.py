# canchas/urls.py
from django.urls import path
from .views import (
    CanchaListView,
    CanchaDetailView,
    CanchaCreateView,
    CanchaUpdateView,
    CanchaDeleteView,
    GestionarDisponibilidadView,
    DisponibilidadSlotsView,
    CalificarCanchaView,
    ReporteCanchasView,
    ReporteCanchasPdfView,
    ReporteCanchasExcelView,
    ReporteCanchasWordView,
    AdminCanchaListView,
    AdminCanchaUpdateView,
    AdminCanchaDeleteView,
    AdminDeporteListView,
    AdminDeporteCreateView,
    AdminDeporteUpdateView,
    AdminDeporteDeleteView,
)

app_name = 'canchas'

urlpatterns = [
    path('', CanchaListView.as_view(), name='lista'),
    path('nueva/', CanchaCreateView.as_view(), name='nueva'),
    path('<int:pk>/', CanchaDetailView.as_view(), name='detalle'),
    path('<int:pk>/editar/', CanchaUpdateView.as_view(), name='editar'),
    path('<int:pk>/eliminar/', CanchaDeleteView.as_view(), name='eliminar'),
    path('<int:pk>/disponibilidad/', GestionarDisponibilidadView.as_view(), name='disponibilidad'),
    path('<int:pk>/slots/', DisponibilidadSlotsView.as_view(), name='slots'),
    path('<int:pk>/calificar/', CalificarCanchaView.as_view(), name='calificar'),
    path('reporte/', ReporteCanchasView.as_view(), name='reporte'),
    path('reporte/pdf/', ReporteCanchasPdfView.as_view(), name='reporte_pdf'),
    path('reporte/excel/', ReporteCanchasExcelView.as_view(), name='reporte_excel'),
    path('reporte/word/', ReporteCanchasWordView.as_view(), name='reporte_word'),
    
    path('gestion/canchas/', AdminCanchaListView.as_view(), name='admin_cancha_list'),
    path('gestion/canchas/<int:pk>/editar/', AdminCanchaUpdateView.as_view(), name='admin_cancha_update'),
    path('gestion/canchas/<int:pk>/eliminar/', AdminCanchaDeleteView.as_view(), name='admin_cancha_delete'),
    
    path('gestion/deportes/', AdminDeporteListView.as_view(), name='admin_deporte_list'),
    path('gestion/deportes/nuevo/', AdminDeporteCreateView.as_view(), name='admin_deporte_create'),
    path('gestion/deportes/<int:pk>/editar/', AdminDeporteUpdateView.as_view(), name='admin_deporte_update'),
    path('gestion/deportes/<int:pk>/eliminar/', AdminDeporteDeleteView.as_view(), name='admin_deporte_delete'),
]
