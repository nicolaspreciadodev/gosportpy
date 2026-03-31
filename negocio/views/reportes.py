import csv
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
