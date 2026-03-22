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
            context['torneos_pendientes'] = Torneo.objects.filter(is_approved=False)
            
        if user.rol == 'DUEÑO':
            context['mis_canchas'] = Cancha.objects.filter(dueño=user)
            context['mis_torneos'] = Torneo.objects.filter(organizador=user)
        elif user.rol == 'DEPORTISTA':
            context['canchas_disponibles'] = Cancha.objects.all()
            context['mis_reservas'] = Reserva.objects.filter(usuario=user)
        
        return context
