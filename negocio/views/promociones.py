from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from core.mixins import RoleRequiredMixin
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from negocio.models import Torneo, PromocionTorneo
from canchas.models import Cancha

class SolicitarPromocionView(RoleRequiredMixin, View):
    """Vista para que un DUEÑO solicite promocionar un torneo en su cancha."""
    allowed_roles = ['DUEÑO']

    def get(self, request, torneo_id):
        torneo = get_object_or_404(Torneo, id=torneo_id, organizador=request.user)
        canchas = torneo.canchas.filter(dueño=request.user)
        return render(request, 'negocio/promociones/solicitar.html', {
            'torneo': torneo,
            'canchas': canchas
        })

    def post(self, request, torneo_id):
        torneo = get_object_or_404(Torneo, id=torneo_id, organizador=request.user)
        cancha_id = request.POST.get('cancha_id')
        texto = request.POST.get('texto_promocional')
        imagen = request.FILES.get('imagen_promocional')

        if not (cancha_id and texto):
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect('negocio:solicitar_promocion', torneo_id=torneo_id)

        cancha = get_object_or_404(Cancha, id=cancha_id, dueño=request.user)
        
        PromocionTorneo.objects.create(
            torneo=torneo,
            cancha=cancha,
            texto_promocional=texto,
            imagen_promocional=imagen
        )

        messages.success(request, "Solicitud de promoción enviada al administrador.")
        return redirect('negocio:mis_torneos')

@method_decorator(user_passes_test(lambda u: u.is_staff), name='dispatch')
class GestionarPromocionView(LoginRequiredMixin, View):
    """Vista para que el ADMIN apruebe o rechace promociones."""
    def post(self, request, promo_id):
        promo = get_object_or_404(PromocionTorneo, id=promo_id)
        accion = request.POST.get('action')

        if accion == 'aprobar':
            promo.estado = 'APROBADO'
            messages.success(request, f"Promoción de {promo.torneo.nombre} aprobada.")
        elif accion == 'rechazar':
            promo.estado = 'RECHAZADO'
            messages.warning(request, f"Promoción de {promo.torneo.nombre} rechazada.")
        
        promo.save()
        return redirect('dashboard')
