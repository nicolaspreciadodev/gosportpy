import json
import hashlib
import hmac
import logging
import requests
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin
from negocio.models import Reserva, Factura
from django.contrib import messages

logger = logging.getLogger(__name__)

class IniciarPagoWompiView(LoginRequiredMixin, View):
    """Renderiza el Widget del Checkout de Wompi.
    Para propósitos del proyecto académico, simula el pago exitoso.
    """
    def get(self, request, reserva_id):
        reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
        
        if reserva.pagado:
            messages.info(request, "Esta reserva ya se encuentra pagada.")
            return redirect('dashboard')
            
        factura = reserva.factura
        if not factura.referencia_pago:
            factura.save()
            
        # Simulación académica: Marcamos como pagado inmediatamente
        reserva.pagado = True
        reserva.estado = 'PROGRAMADA'
        reserva.save()
        
        # Enviar notificación simulada
        try:
            from core.emails import enviar_confirmacion_reserva
            enviar_confirmacion_reserva(reserva)
        except Exception as e:
            logger.error(f"Error enviando confirmación: {e}")

        messages.success(request, "¡Pago con Wompi simulado exitosamente!")
        return render(request, 'negocio/pagos/pago_exitoso.html', {
            'reserva': reserva,
            'factura': factura
        })

class RespuestaPagoWompiView(LoginRequiredMixin, View):
    """Vista de retorno del usuario después del Checkout."""
    def get(self, request):
        return redirect('dashboard')

@method_decorator(csrf_exempt, name='dispatch')
class WebhookWompiView(View):
    """Webhook para recibir notificaciones asíncronas de Wompi."""
    def post(self, request, *args, **kwargs):
        return JsonResponse({'status': 'ok'})
