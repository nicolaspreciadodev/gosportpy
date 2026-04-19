from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from canchas.models import Cancha, Deporte
from negocio.models import Reserva, Torneo
from usuarios.models import CustomUser

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.is_superuser:
            context['is_admin'] = True
            context['total_usuarios'] = CustomUser.objects.count()
            context['total_canchas'] = Cancha.objects.count()
            context['total_reservas'] = Reserva.objects.count()
            context['torneos_pendientes'] = Torneo.objects.filter(estado='PENDIENTE')
            from negocio.models import SolicitudModificacionTorneo
            context['solicitudes_modificacion'] = SolicitudModificacionTorneo.objects.filter(estado='PENDIENTE')
            
        if user.rol == 'DUEÑO':
            context['mis_canchas'] = Cancha.objects.filter(dueño=user)
            context['mis_torneos'] = Torneo.objects.filter(organizador=user)
        elif user.rol == 'DEPORTISTA':
            context['canchas_disponibles'] = Cancha.objects.all()
            context['mis_reservas'] = Reserva.objects.filter(usuario=user)
        
        return context

import json
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Q

class AdminAnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'core/admin_analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.request.user.is_superuser:
            return context
        
        ahora = timezone.now()
        hace_30_dias = ahora - timedelta(days=30)
        
        reservas_pagadas = Reserva.objects.filter(Q(pagado=True) | Q(estado='COMPLETADA'))
        ingresos_totales = reservas_pagadas.aggregate(total=Sum('factura__total'))['total'] or 0.0
        
        reservas_mes = reservas_pagadas.filter(fecha__year=ahora.year, fecha__month=ahora.month)
        ingresos_mes = reservas_mes.aggregate(total=Sum('factura__total'))['total'] or 0.0

        reservas_ultimos_30 = Reserva.objects.filter(
            fecha__gte=hace_30_dias.date(),
            estado__in=['PROGRAMADA', 'COMPLETADA']
        )
        total_reservas_30_dias = reservas_ultimos_30.count()
        reservas_por_dia = reservas_ultimos_30.values('fecha').annotate(
            cantidad=Count('id')
        ).order_by('fecha')
        
        dias_labels = [r['fecha'].strftime('%d %b') for r in reservas_por_dia]
        dias_data = [r['cantidad'] for r in reservas_por_dia]

        roles_data = CustomUser.objects.values('rol').annotate(total=Count('id'))
        roles_labels = [item['rol'] for item in roles_data]
        roles_counts = [item['total'] for item in roles_data]

        canchas_populares = Cancha.objects.annotate(
            num_reservas=Count('reservas')
        ).filter(num_reservas__gt=0).order_by('-num_reservas')[:5]
        
        canchas_labels = [c.nombre for c in canchas_populares]
        canchas_data_counts = [c.num_reservas for c in canchas_populares]

        context.update({
            'ingresos_totales': float(ingresos_totales),
            'ingresos_mes': float(ingresos_mes),
            'total_reservas_30_dias': total_reservas_30_dias,
            'dias_labels_json': json.dumps(dias_labels),
            'dias_data_json': json.dumps(dias_data),
            'roles_labels_json': json.dumps(roles_labels),
            'roles_counts_json': json.dumps(roles_counts),
            'canchas_labels_json': json.dumps(canchas_labels),
            'canchas_data_json': json.dumps(canchas_data_counts),
        })
        return context
