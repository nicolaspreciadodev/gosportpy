import mercadopago
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from negocio.models import Reserva
from django.contrib import messages

class IniciarPagoView(LoginRequiredMixin, View):
    """Genera la preferencia en MercadoPago y renderiza el Widget del Checkout."""
    def get(self, request, reserva_id):
        reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
        
        if reserva.pagado:
            messages.info(request, "Esta reserva ya se encuentra pagada.")
            return redirect('dashboard')
            
        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
        
        host = request.build_absolute_uri('/')[:-1]
        
        preference_data = {
            "items": [
                {
                    "title": f"Reserva de Cancha: {reserva.cancha.nombre}",
                    "quantity": 1,
                    "unit_price": float(reserva.cancha.precio)
                }
            ],
            "payer": {
                "name": request.user.first_name,
                "email": request.user.email
            },
            "back_urls": {
                "success": f"{host}/negocio/pagos/exito/?reserva_id={reserva.id}",
                "failure": f"{host}/negocio/pagos/fallo/",
                "pending": f"{host}/negocio/pagos/pendiente/"
            },
            "auto_return": "approved",
            "external_reference": str(reserva.id)
        }
        
        preference_response = sdk.preference().create(preference_data)
        
        # En caso de error contactando a la API de MP
        if preference_response.get("status") != 201:
            messages.error(request, "Ocurrió un error inicializando el pago. Intenta de nuevo más tarde.")
            return redirect('dashboard')
            
        preference = preference_response["response"]
        
        context = {
            'reserva': reserva,
            'preference_id': preference['id'],
            'public_key': settings.MERCADOPAGO_PUBLIC_KEY
        }
        
        return render(request, 'negocio/pagos/checkout.html', context)

class PagoExitosoView(LoginRequiredMixin, View):
    """Vista de retorno (success back_url) desde MercadoPago."""
    def get(self, request):
        reserva_id = request.GET.get('reserva_id')
        payment_id = request.GET.get('payment_id')
        status = request.GET.get('status')
        
        reserva = None
        if reserva_id and status == 'approved':
            reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
            reserva.pagado = True
            reserva.save()
            messages.success(request, f"Pago aprobado (ID: {payment_id}). ¡Tu reserva está asegurada!")
            
        return render(request, 'negocio/pagos/pago_exitoso.html', {
            'reserva': reserva,
            'payment_id': payment_id
        })

class PagoFallidoView(LoginRequiredMixin, View):
    """Vista de retorno (failure back_url) desde MercadoPago."""
    def get(self, request):
        messages.error(request, "Tu pago fue rechazado. Revisa tus fondos e intenta nuevamente.")
        return render(request, 'negocio/pagos/pago_fallido.html')

class PagoPendienteView(LoginRequiredMixin, View):
    """Vista de retorno (pending back_url) desde MercadoPago."""
    def get(self, request):
        messages.warning(request, "Tu pago está pendiente de aprobación. Se notificará cuando se procese.")
        return render(request, 'negocio/pagos/pago_pendiente.html')
