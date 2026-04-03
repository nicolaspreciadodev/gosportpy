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


# ====================================================
# EXPORTACIONES DE RESERVAS MULTIFORMATO
# ====================================================

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import openpyxl
from docx import Document
from django.contrib.auth.mixins import LoginRequiredMixin

def get_reservas_por_rol(user):
    """Devuelve las reservas permitidas dependiendo del perfil."""
    if user.is_superuser or user.rol == 'ADMIN':
        return Reserva.objects.all().order_by('-fecha', '-hora')
    elif user.rol == 'DUEÑO':
        return Reserva.objects.filter(cancha__dueño=user).order_by('-fecha', '-hora')
    else:  # DEPORTISTA
        return Reserva.objects.filter(usuario=user).order_by('-fecha', '-hora')


class ReporteReservasPdfView(LoginRequiredMixin, View):
    def get(self, request):
        reservas = get_reservas_por_rol(request.user)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="reporte_reservas.pdf"'

        p = canvas.Canvas(response, pagesize=letter)
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, 750, f"Reporte de Reservas - GoSport2 ({request.user.rol})")
        
        p.setFont("Helvetica", 10)
        y = 710
        for idx, r in enumerate(reservas):
            texto = f"{idx+1}. Cancha: {r.cancha.nombre} | Deportista: {r.usuario.username} | Fecha: {r.fecha} {r.hora} | Estado: {r.estado} | Pagado: {'Sí' if r.pagado else 'No'}"
            p.drawString(80, y, texto)
            y -= 20
            if y < 50:  # Nueva página si se acaba el espacio
                p.showPage()
                p.setFont("Helvetica", 10)
                y = 750

        p.showPage()
        p.save()

        return response


class ReporteReservasExcelView(LoginRequiredMixin, View):
    def get(self, request):
        reservas = get_reservas_por_rol(request.user)

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="reporte_reservas.xlsx"'

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Reservas"
        
        ws.append(["ID", "Cancha", "Deportista", "Fecha", "Hora", "Estado", "Monto Total", "Pagado"])
        
        for r in reservas:
            monto_total = r.factura.total if hasattr(r, 'factura') else 0.0
            ws.append([
                r.id, r.cancha.nombre, r.usuario.email, 
                r.fecha, r.hora, r.estado, monto_total, 'Sí' if r.pagado else 'No'
            ])
            
        wb.save(response)
        return response


class ReporteReservasWordView(LoginRequiredMixin, View):
    def get(self, request):
        reservas = get_reservas_por_rol(request.user)

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = 'attachment; filename="reporte_reservas.docx"'

        doc = Document()
        doc.add_heading(f'Reporte de Reservas ({request.user.rol}) - GoSport2', 0)
        
        table = doc.add_table(rows=1, cols=5)
        table.style = 'Table Grid'
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'ID'
        hdr_cells[1].text = 'Cancha'
        hdr_cells[2].text = 'Deportista'
        hdr_cells[3].text = 'Fecha'
        hdr_cells[4].text = 'Estado'
        
        for r in reservas:
            row_cells = table.add_row().cells
            row_cells[0].text = str(r.id)
            row_cells[1].text = r.cancha.nombre
            row_cells[2].text = r.usuario.get_full_name() or r.usuario.username
            row_cells[3].text = f"{r.fecha} {r.hora.strftime('%H:%M')}"
            row_cells[4].text = str(r.estado)
            
        doc.save(response)
        return response
