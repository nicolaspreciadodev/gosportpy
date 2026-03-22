from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins import RoleRequiredMixin
from django.contrib import messages
from canchas.models import Cancha
from .models import Reserva, Factura
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
