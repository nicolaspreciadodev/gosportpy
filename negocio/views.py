from django.shortcuts import render, get_object_or_404, redirect
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins import RoleRequiredMixin
from django.contrib import messages
from canchas.models import Cancha
from .models import Reserva, Factura, Torneo, Equipo
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator


@method_decorator(user_passes_test(lambda u: u.is_staff), name='dispatch')
class AprobarTorneoView(LoginRequiredMixin, View):
    """Vista para que un ADMINISTRADOR apruebe o rechace un torneo."""

    def post(self, request, torneo_id):
        torneo = get_object_or_404(Torneo, id=torneo_id)
        accion = request.POST.get('accion')  # 'aprobar' o 'rechazar'

        if accion == 'aprobar':
            torneo.estado = 'PUBLICADO'
            messages.success(request, f'El torneo "{torneo.nombre}" ha sido aprobado y publicado.')
        elif accion == 'rechazar':
            torneo.estado = 'RECHAZADO'
            messages.warning(request, f'El torneo "{torneo.nombre}" ha sido rechazado.')
        else:
            messages.error(request, 'Acción no válida.')
            return redirect('dashboard') # O a la página de detalle del torneo

        torneo.save()
        return redirect('dashboard') # Redirigir a una página de administración de torneos o dashboard


class CrearReservaView(RoleRequiredMixin, View):
    """Vista para que un DEPORTISTA cree una reserva en una cancha."""
    allowed_roles = ['DEPORTISTA']

    def get(self, request, cancha_id):
        cancha = get_object_or_404(Cancha, id=cancha_id)
        return render(request, 'crear_reserva.html', {'cancha': cancha})

    def post(self, request, cancha_id):
        cancha = get_object_or_404(Cancha, id=cancha_id)
        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora')

        if not fecha or not hora:
            messages.error(request, 'Debe proporcionar una fecha y hora.')
            return render(request, 'crear_reserva.html', {'cancha': cancha})

        reserva = Reserva(usuario=request.user, cancha=cancha, fecha=fecha, hora=hora)

        try:
            reserva.full_clean()
            reserva.save()
            messages.success(request, '¡Reserva creada con éxito!')
            return redirect('dashboard')
        except ValidationError as e:
            for msg in e.messages:
                messages.error(request, msg)
            return render(request, 'crear_reserva.html', {'cancha': cancha})


class FacturaDetalleView(LoginRequiredMixin, View):
    """Vista para que un usuario vea el detalle de su factura.

    Solo el dueño de la reserva puede ver su factura (evita acceso cruzado).
    """

    def get(self, request, factura_id):
        factura = get_object_or_404(Factura, id=factura_id)
        reserva = factura.reserva

        # 🔒 Solo el propietario de la reserva puede ver su factura
        if reserva.usuario != request.user:
            messages.error(request, 'No tienes permiso para ver esta factura.')
            return redirect('dashboard')

        return render(request, 'factura_detalle.html', {
            'factura': factura,
            'reserva': reserva,
        })

class CancelarReservaView(LoginRequiredMixin, View):
    """Vista para que un DEPORTISTA o DUEÑO cancele una reserva si cumple las reglas."""
    def post(self, request, reserva_id):
        reserva = get_object_or_404(Reserva, id=reserva_id)

        # Solo el dueño de la reserva o el dueño de la cancha pueden cancelarla
        es_dueno_reserva = reserva.usuario == request.user
        es_dueno_cancha = reserva.cancha.dueño == request.user

        if not (es_dueno_reserva or es_dueno_cancha):
            messages.error(request, 'No tienes permiso para cancelar esta reserva.')
            return redirect('dashboard')

        if reserva.estado == 'CANCELADA':
            messages.error(request, 'Esta reserva ya se encuentra cancelada.')
            return redirect('dashboard')
            
        if reserva.estado == 'COMPLETADA':
            messages.error(request, 'Esta reserva ya se completó, no puede ser cancelada.')
            return redirect('dashboard')

        # Si es el deportista, validamos las 24 horas. El dueño puede obviar esto, o también aplicamos regla general.
        # Aplicamos la regla a todos según el requisito.
        if not reserva.puede_cancelar():
            messages.error(request, 'Solo puedes cancelar con al menos 24 horas de anticipación.')
            return redirect('dashboard')

        # Si todo es válido
        reserva.estado = 'CANCELADA'
        reserva.save()
        messages.success(request, 'La reserva ha sido cancelada exitosamente y el horario fue liberado.')
        return redirect('dashboard')

class InscribirEquipoView(LoginRequiredMixin, View):
    """Vista para que un miembro de un equipo inscriba al equipo en un torneo."""
    def post(self, request, torneo_id):
        torneo = get_object_or_404(Torneo, id=torneo_id)
        equipo_id = request.POST.get('equipo_id')
        
        if not equipo_id:
            messages.error(request, 'Debe seleccionar un equipo válido.')
            return redirect('dashboard')
            
        equipo = get_object_or_404(Equipo, id=equipo_id)
        
        # Validar permisos: el usuario debe pertenecer al equipo
        if request.user not in equipo.jugadores.all():
            messages.error(request, 'No tienes permiso para inscribir este equipo, ya que no perteneces a sus jugadores.')
            return redirect('dashboard')
            
        # Validar que el torneo esté publicado
        if torneo.estado != 'PUBLICADO':
            messages.error(request, 'El torneo no está abierto para inscripciones.')
            return redirect('dashboard')
            
        # Validar si el equipo ya está inscrito
        if equipo.torneos.filter(id=torneo.id).exists():
            messages.error(request, 'Tu equipo ya está inscrito en este torneo.')
            return redirect('dashboard')
            
        # Realizar inscripción
        equipo.torneos.add(torneo)
        messages.success(request, f'¡El equipo {equipo.nombre} ha sido inscrito en el torneo {torneo.nombre} exitosamente!')
        return redirect('dashboard')
