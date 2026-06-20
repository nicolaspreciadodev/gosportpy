import json
import hashlib
import hmac
import logging
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
        
        # Validar configuración enviando variables
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
        status = request.GET.get('status', 'UNKNOWN')
        
        # Buscaremos la factura y reserva por si no hay status en la url
        factura = Factura.objects.filter(wompi_transaction_id=transaction_id).first()
        reserva = factura.reserva if factura else None
        
        logger.info(f"Respuesta de pago recibida: {transaction_id}, status: {status}")
        
        if status == 'APPROVED':
            messages.success(request, "¡Pago exitoso! Tu reserva está confirmada.")
        elif status == 'DECLINED':
            messages.error(request, "El pago fue rechazado. Por favor intenta de nuevo.")
        else:
            messages.info(request, "Verificando el estado de tu transacción. Si fue exitosa se reflejará en tus reservas pronto.")
        
        return render(request, 'negocio/pagos/pago_respuesta.html', {
            'transaction_id': transaction_id,
            'reserva': reserva,
            'status': status
        })

@method_decorator(csrf_exempt, name='dispatch')
class WebhookWompiView(View):
    """Webhook para recibir notificaciones asincronas de Wompi."""
    
    def _verify_signature(self, payload_body, signature):
        """Verifica la firma de integridad (HMAC-SHA256) del webhook de Wompi."""
        try:
            events_secret = getattr(settings, 'WOMPI_EVENTS_SECRET', 'test_events_XXXXX')
            
            # Crear firma esperada: HMAC-SHA256(payload_body, WOMPI_EVENTS_SECRET)
            expected_signature = hmac.new(
                events_secret.encode(),
                payload_body.encode() if isinstance(payload_body, str) else payload_body,
                hashlib.sha256
            ).hexdigest()
            
            # Comparar con signature recibida
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Error verificando firma de Wompi: {str(e)}")
            return False
    
    def post(self, request, *args, **kwargs):
        try:
            # Obtener la firma del header
            signature = request.META.get('HTTP_X_SIGNATURE', None)
            
            if not signature:
                logger.warning("Webhook recibido sin firma (X-Signature header faltante)")
                return JsonResponse({'error': 'Signature required'}, status=400)
            
            # Obtener el body raw
            payload_body = request.body.decode('utf-8')
            payload = json.loads(payload_body)
            
            # Verificar la firma
            if not self._verify_signature(payload_body, signature):
                logger.warning(f"Firma de Wompi inválida: {signature}")
                return JsonResponse({'error': 'Invalid signature'}, status=403)
            
            logger.info(f"Firma de Wompi verificada correctamente")
            
            # Procesar el evento
            event = payload.get('event')
            data = payload.get('data', {}).get('transaction', {})
            
            if event == 'transaction.updated':
                ref = data.get('reference')
                status = data.get('status')
                transaction_id = data.get('id')
                
                logger.info(f"Transacción actualizada - Ref: {ref}, Status: {status}, ID: {transaction_id}")
                
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
                            
                            logger.info(f"Reserva {reserva.id} marcada como pagada")
                    except Factura.DoesNotExist:
                        logger.error(f"Factura no encontrada con referencia: {ref}")
                elif status == 'DECLINED':
                    logger.warning(f"Transacción rechazada - Ref: {ref}")
                        
            return JsonResponse({'status': 'ok'})
        except json.JSONDecodeError:
            logger.error("Error: payload no es JSON válido")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error en webhook de Wompi: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
