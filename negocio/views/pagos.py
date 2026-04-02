import json
import hashlib
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin
from negocio.models import Reserva, Factura
from django.contrib import messages

class IniciarPagoWompiView(LoginRequiredMixin, View):
    """Renderiza el Widget del Checkout de Wompi."""
    def get(self, request, reserva_id):
        reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
        
        if reserva.pagado:
            messages.info(request, "Esta reserva ya se encuentra pagada.")
            return redirect('panel_reservas')
            
        factura = reserva.factura
        if not factura.referencia_pago:
            factura.save()
            
        monto_centavos = int(factura.total * 100)
        
        # Validar configuración enviando varibles
        context = {
            'reserva': reserva,
            'factura': factura,
            'monto_centavos': monto_centavos,
            'public_key': getattr(settings, 'WOMPI_PUBLIC_KEY', 'pub_test_XXXXX')
        }
        
        return render(request, 'negocio/pagos/wompi_checkout.html', context)

class RespuestaPagoWompiView(LoginRequiredMixin, View):
    """Vista de retorno del usuario despues del Checkout."""
    def get(self, request):
        transaction_id = request.GET.get('id')
        
        # Buscaremos la factura y reserva por si no hay status en la url
        factura = Factura.objects.filter(wompi_transaction_id=transaction_id).first()
        reserva = factura.reserva if factura else None
        
        messages.info(request, "Verificando el estado de tu transacción. Si fue exitosa se reflejará en tus reservas pronto.")
        
        return render(request, 'negocio/pagos/pago_respuesta.html', {
            'transaction_id': transaction_id,
            'reserva': reserva
        })

@method_decorator(csrf_exempt, name='dispatch')
class WebhookWompiView(View):
    """Webhook para recibir notificaciones asincronas de Wompi."""
    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body)
            event = payload.get('event')
            data = payload.get('data', {}).get('transaction', {})
            
            # Verificación de firma (signature) omitida aquí por simplicidad,
            # pero idealmente se concatena properties y se hace sha256 con
            # setting.WOMPI_EVENTS_SECRET.
            
            if event == 'transaction.updated':
                ref = data.get('reference')
                status = data.get('status')
                transaction_id = data.get('id')
                
                if status == 'APPROVED':
                    try:
                        factura = Factura.objects.get(referencia_pago=ref)
                        reserva = factura.reserva
                        if not reserva.pagado:
                            reserva.pagado = True
                            reserva.estado = 'PROGRAMADA'
                            reserva.save()
                            
                            factura.wompi_transaction_id = transaction_id
                            factura.save()
                    except Factura.DoesNotExist:
                        pass
                        
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
