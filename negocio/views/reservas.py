from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins import RoleRequiredMixin
from django.contrib import messages
from canchas.models import Cancha
from negocio.models import Reserva, Factura
from django.core.exceptions import ValidationError

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

        from datetime import datetime
        import datetime as dt
        from django.utils import timezone
        
        try:
            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
            if fecha_obj > timezone.now().date() + dt.timedelta(days=30):
                messages.error(request, 'No puedes hacer reservas con más de 30 días (1 mes) de anticipación.')
                return render(request, 'crear_reserva.html', {'cancha': cancha})
        except ValueError:
            messages.error(request, 'Formato de fecha inválido.')
            return render(request, 'crear_reserva.html', {'cancha': cancha})

        from canchas.services import validar_slot_disponible
        if not validar_slot_disponible(cancha_id, fecha, hora):
            messages.error(request, 'El horario seleccionado no está disponible o es inválido.')
            return render(request, 'crear_reserva.html', {'cancha': cancha})

        reserva = Reserva(usuario=request.user, cancha=cancha, fecha=fecha, hora=hora)

        try:
            reserva.full_clean()
            reserva.save()
            
            try:
                from core.emails import enviar_confirmacion_reserva
                enviar_confirmacion_reserva(reserva)
            except Exception as ex:
                import logging
                logging.getLogger('django').error(f"Error enviando email de confirmación: {ex}")

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

        if not reserva.puede_cancelar():
            messages.error(request, 'Solo puedes cancelar con al menos 24 horas de anticipación.')
            return redirect('dashboard')

        reserva.estado = 'CANCELADA'
        reserva.save()
        messages.success(request, 'La reserva ha sido cancelada exitosamente y el horario fue liberado.')
        return redirect('dashboard')


class PanelReservasView(RoleRequiredMixin, View):
    """Vista para que el DUEÑO vea y filtre las reservas de TODAS sus canchas."""
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

        context = {
            'reservas': reservas,
            'estado_activo': estado_filter,
            'fecha_activa': fecha_filter,
            'cancha_activa': cancha_filter,
            'canchas': canchas_dueño,
        }
        return render(request, 'panel_reservas.html', context)


class SimularPagoView(LoginRequiredMixin, View):
    """Vista para simular el pago de una reserva."""
    def post(self, request, reserva_id):
        reserva = get_object_or_404(Reserva, id=reserva_id)

        if reserva.usuario != request.user:
            messages.error(request, 'No tienes permiso para pagar esta reserva.')
            return redirect('dashboard')

        if reserva.pagado:
            messages.warning(request, 'Esta reserva ya se encuentra pagada.')
            return redirect('dashboard')

        if reserva.estado != 'PROGRAMADA':
            messages.error(request, 'Solo las reservas programadas pueden ser pagadas.')
            return redirect('dashboard')

        reserva.pagado = True
        reserva.save()

        messages.success(request, '¡El pago ha sido procesado exitosamente!')
        return redirect('negocio:factura_detalle', factura_id=reserva.factura.id)
