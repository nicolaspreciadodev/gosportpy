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
]
