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
    """Vista de retorno del usuario despues del Checkout.
    
    NOTA: Esta vista es la que procesa el pago sin depender de webhooks.
    Consulta directamente a la API de Wompi para verificar el estado.
    """
    
    def _consultar_wompi(self, transaction_id):
        """Consulta directamente a Wompi para obtener el estado de la transacción."""
        try:
            private_key = getattr(settings, 'WOMPI_PRIVATE_KEY', 'prv_test_XXXXX')
            
            response = requests.get(
                f'https://api.wompi.co/v1/transactions/{transaction_id}',
                headers={
                    'Authorization': f'Bearer {private_key}',
                    'Content-Type': 'application/json'
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                transaction = data.get('data', {})
                return {
                    'status': transaction.get('status'),
                    'reference': transaction.get('reference'),
                    'id': transaction.get('id'),
                    'amount_in_cents': transaction.get('amount_in_cents'),
                    'payment_method': transaction.get('payment_method', {}).get('type')
                }
            else:
                logger.error(f"Error consultando Wompi: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Excepción consultando Wompi: {str(e)}")
            return None
    
    def get(self, request):
        transaction_id = request.GET.get('id')
        
        if not transaction_id:
            messages.error(request, "Error: No se proporcionó ID de transacción.")
            return redirect('negocio:panel_reservas')
        
        # Consultar a Wompi directamente
        wompi_data = self._consultar_wompi(transaction_id)
        
        if not wompi_data:
            messages.warning(request, "No pudimos verificar el estado de tu transacción. Por favor contacta soporte.")
            logger.warning(f"No se pudo consultar Wompi para transacción: {transaction_id}")
            return render(request, 'negocio/pagos/pago_respuesta.html', {
                'transaction_id': transaction_id,
                'reserva': None,
                'status': 'UNKNOWN'
            })
        
        # Buscar la factura por referencia
        ref = wompi_data.get('reference')
        factura = Factura.objects.filter(referencia_pago=ref).first()
        reserva = factura.reserva if factura else None
        status = wompi_data.get('status')
        
        logger.info(f"Transacción {transaction_id}: {status}, Referencia: {ref}, Reserva: {reserva.id if reserva else 'No encontrada'}")
        
        # Procesar según el estado
        if status == 'APPROVED':
            if reserva and not reserva.pagado:
                reserva.pagado = True
                reserva.estado = 'PROGRAMADA'
                reserva.save()
                
                if factura:
                    factura.wompi_transaction_id = transaction_id
                    factura.save()
                
                logger.info(f"✅ Reserva {reserva.id} marcada como PAGADA")
                messages.success(request, f"¡Pago exitoso! Tu reserva en {reserva.cancha.nombre} está confirmada.")
            elif reserva and reserva.pagado:
                messages.info(request, "Esta reserva ya se encuentra pagada.")
        
        elif status == 'DECLINED':
            messages.error(request, "El pago fue rechazado. Por favor intenta de nuevo.")
            logger.warning(f"Pago rechazado: {transaction_id}")
        
        elif status == 'PENDING':
            messages.info(request, "Tu pago está siendo procesado. Te notificaremos cuando se complete.")
            logger.info(f"Pago pendiente: {transaction_id}")
        
        else:
            messages.warning(request, f"Estado de pago desconocido: {status}")
            logger.warning(f"Estado desconocido para transacción {transaction_id}: {status}")
        
        return render(request, 'negocio/pagos/pago_respuesta.html', {
            'transaction_id': transaction_id,
            'reserva': reserva,
            'status': status,
            'wompi_data': wompi_data
        })

@method_decorator(csrf_exempt, name='dispatch')
class WebhookWompiView(View):
    """Webhook para recibir notificaciones asincronas de Wompi.
    
    NOTA: Este webhook es OPCIONAL. El sistema funciona sin él.
    Si Wompi lo llama, procesamos la transacción de forma redundante.
    """
    
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
            # Obtener la firma del header (opcional)
            signature = request.META.get('HTTP_X_SIGNATURE', None)
            
            # Obtener el body raw
            payload_body = request.body.decode('utf-8')
            payload = json.loads(payload_body)
            
            # Si hay firma, verificarla (pero no es obligatorio)
            if signature and not self._verify_signature(payload_body, signature):
                logger.warning(f"Firma de Wompi inválida: {signature}")
                return JsonResponse({'error': 'Invalid signature'}, status=403)
            
            if signature:
                logger.info(f"✅ Firma de Wompi verificada correctamente")
            
            # Procesar el evento
            event = payload.get('event')
            data = payload.get('data', {}).get('transaction', {})
            
            if event == 'transaction.updated':
                ref = data.get('reference')
                status = data.get('status')
                transaction_id = data.get('id')
                
                logger.info(f"Webhook recibido - Event: {event}, Ref: {ref}, Status: {status}, ID: {transaction_id}")
                
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
                            
                            logger.info(f"✅ Webhook procesado: Reserva {reserva.id} marcada como pagada")
                    except Factura.DoesNotExist:
                        logger.error(f"Factura no encontrada con referencia: {ref}")
                elif status == 'DECLINED':
                    logger.warning(f"Webhook: Transacción rechazada - Ref: {ref}")
                        
            return JsonResponse({'status': 'ok'})
        except json.JSONDecodeError:
            logger.error("Error: payload no es JSON válido")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error en webhook de Wompi: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
        
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
