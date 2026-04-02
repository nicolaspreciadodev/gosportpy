import csv
import json
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from core.mixins import RoleRequiredMixin
from canchas.models import Cancha
from negocio.models import Reserva, Torneo

class ReporteReservasView(RoleRequiredMixin, View):
    allowed_roles = ['DUEÑO']
    
    def get(self, request):
        canchas_dueño = Cancha.objects.filter(dueño=request.user)
        reservas = Reserva.objects.filter(cancha__in=canchas_dueño).order_by('-fecha', '-hora')

        estado_filter = request.GET.get('estado')
        if estado_filter:
            reservas = reservas.filter(estado=estado_filter)

        fecha_filter = request.GET.get('fecha')
        if fecha_filter:
            reservas = reservas.filter(fecha=fecha_filter)

        cancha_filter = request.GET.get('cancha_id')
        if cancha_filter:
            try:
                reservas = reservas.filter(cancha__id=int(cancha_filter))
            except ValueError:
                pass

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reporte_reservas.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Cancha', 'Deportista', 'Fecha', 'Hora', 'Estado', 'Pagado'])

        for r in reservas:
            writer.writerow([r.id, r.cancha.nombre, r.usuario.email, r.fecha, r.hora, r.estado, 'Sí' if r.pagado else 'No'])

        return response


class ReporteTorneosView(RoleRequiredMixin, View):
    allowed_roles = ['DUEÑO']
    
    def get(self, request):
        torneos = Torneo.objects.filter(organizador=request.user).order_by('-fecha_inicio')

        torneo_q = request.GET.get('torneo_q')
        if torneo_q:
            torneos = torneos.filter(nombre__icontains=torneo_q)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reporte_torneos.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Nombre', 'Deporte', 'Estado', 'Equipos Inscritos', 'Max Equipos'])

        for t in torneos:
            writer.writerow([t.id, t.nombre, t.deporte.nombre, t.estado, t.equipos.count(), t.max_equipos])

        return response


class PanelAnalyticsView(RoleRequiredMixin, View):
    """Panel estadístico para el DUEÑO.
    
    Calcula ingresos (basados en reservas pagadas/completadas)
    y genera JSON para ser leídos por Chart.js en el frontend.
    """
    allowed_roles = ['DUEÑO']
    
    def get(self, request):
        ahora = timezone.now()
        hace_30_dias = ahora - timedelta(days=30)
        
        canchas_dueño = Cancha.objects.filter(dueño=request.user)
        
        # Reservas históricas válidas para ingreso (Pagadas o Completadas)
        reservas_ingresos = Reserva.objects.filter(
            cancha__in=canchas_dueño
        ).filter(
            Q(pagado=True) | Q(estado='COMPLETADA')
        )
        
        # 1. Ingresos Totales Históricos
        ingresos_totales = reservas_ingresos.aggregate(
            total=Sum('factura__total')
        )['total'] or 0.0

        # 2. Ingresos del Mes Actual
        reservas_mes = reservas_ingresos.filter(
            fecha__year=ahora.year, 
            fecha__month=ahora.month
        )
        ingresos_mes = reservas_mes.aggregate(
            total=Sum('factura__total')
        )['total'] or 0.0
        
        # 3. Reservas Confirmadas Últimos 30 días
        reservas_ultimos_30 = Reserva.objects.filter(
            cancha__in=canchas_dueño,
            fecha__gte=hace_30_dias.date(),
            estado__in=['PROGRAMADA', 'COMPLETADA']
        )
        total_reservas_30_dias = reservas_ultimos_30.count()
        
        # 4. Datos Gráfico: Reservas por Día (Últimos 30)
        reservas_por_dia = reservas_ultimos_30.values('fecha').annotate(
            cantidad=Count('id')
        ).order_by('fecha')
        
        dias_labels = [r['fecha'].strftime('%d %b') for r in reservas_por_dia]
        dias_data = [r['cantidad'] for r in reservas_por_dia]
        
        # 5. Datos Gráfico: Reservas por Cancha (Doughnut)
        canchas_populares = Cancha.objects.filter(
            dueño=request.user
        ).annotate(
            num_reservas=Count('reservas')
        ).filter(num_reservas__gt=0).order_by('-num_reservas')
        
        canchas_labels = [c.nombre for c in canchas_populares]
        canchas_data = [c.num_reservas for c in canchas_populares]

        context = {
            'ingresos_totales': float(ingresos_totales),
            'ingresos_mes': float(ingresos_mes),
            'total_reservas_30_dias': total_reservas_30_dias,
            
            # JSON Data para Chart.js
            'dias_labels_json': json.dumps(dias_labels),
            'dias_data_json': json.dumps(dias_data),
            'canchas_labels_json': json.dumps(canchas_labels),
            'canchas_data_json': json.dumps(canchas_data),
        }
        
        return render(request, 'analytics.html', context)
