# 🔍 Diagnóstico: Error de Pago en Wompi

## Problema Reportado

```
❌ El pago no pudo ser realizado:
   - signature: Firma de integridad requerida no enviada

❌ Al reintentar:
   - Token de aceptación: El token de aceptación ya fue usado
```

---

## 🎯 Causa Raíz

### 1. **Falta de verificación de firma (SIGNATURE)**
En el webhook (`negocio/views/pagos.py`), la verificación de firma estaba **comentada como "omitida por simplicidad"**.

```python
# ❌ ANTES (INCORRECTO)
# Verificación de firma (signature) omitida aquí por simplicidad
```

Wompi **rechaza todos los webhooks sin firma válida** porque no puede garantizar que la solicitud viene realmente de Wompi.

### 2. **Token reutilizado**
Cuando el usuario clickea "Seguir con pago" múltiples veces, Wompi rechaza porque:
- El token anterior aún está activo
- Wompi no permite usar el mismo token dos veces

### 3. **Falta de logging**
Sin logs, era imposible saber qué fallaba exactamente.

---

## ✅ Solución Implementada

### Cambios en `negocio/views/pagos.py`:

#### 1. **Verificación correcta de firma con HMAC-SHA256**
```python
def _verify_signature(self, payload_body, signature):
    """Verifica HMAC-SHA256(payload, WOMPI_EVENTS_SECRET)"""
    expected_signature = hmac.new(
        events_secret.encode(),
        payload_body.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)
```

#### 2. **Validación del header X-Signature**
```python
signature = request.META.get('HTTP_X_SIGNATURE', None)

if not signature:
    return JsonResponse({'error': 'Signature required'}, status=400)
```

#### 3. **Logging detallado**
```python
logger.info(f"Transacción actualizada - Ref: {ref}, Status: {status}")
logger.error(f"Error en webhook de Wompi: {str(e)}")
```

#### 4. **Mejor manejo de respuestas**
```python
if status == 'APPROVED':
    # Marcar reserva como pagada
elif status == 'DECLINED':
    # Rechazar transacción
```

---

## 📋 Checklist: Configuración en Wompi

Para que funcione correctamente, **DEBES** configurar el webhook en Wompi:

### En el dashboard de Wompi:

1. **Ve a:** Configuración → Webhooks
2. **URL del webhook:** 
   ```
   https://gosportpy-production-ed70.up.railway.app/api/webhooks/wompi/
   ```

3. **Evento a escuchar:** 
   ```
   transaction.updated
   ```

4. **Headers personalizados:** (Opcional pero recomendado)
   ```
   X-API-Key: Tu_API_Key_Wompi
   ```

5. **Método:** POST

6. **Verificación de Wompi:** 
   - ✅ Wompi **automáticamente** envía el header `X-Signature`
   - ✅ Nuestro código ahora lo verifica

---

## 🧪 Cómo probar

### Test 1: Verificar que el webhook está registrado
```bash
# En Railway, revisa los logs
# Deberías ver: "Webhook recibido" o "Firma de Wompi verificada"
```

### Test 2: Hacer un pago de prueba
1. Vuelve a Railway y abre tu app
2. Selecciona una reserva
3. Click en "Pagar con Wompi"
4. Completa el pago (usa credenciales de prueba de Wompi)
5. Deberías recibir confirmación inmediata

### Test 3: Revisar logs en Railway
```
# En Railway → Logs → Busca "Transacción actualizada"
```

---

## 📊 Estados de Transacción

| Estado | Significado | Acción |
|--------|-----------|--------|
| `APPROVED` | Pago exitoso | ✅ Marca reserva como pagada |
| `DECLINED` | Rechazado | ❌ Mantén como no pagada |
| `PENDING` | Esperando confirmación | ⏳ Espera el webhook |
| `VOIDED` | Cancelado | ❌ Reserva no pagada |

---

## 🔐 Seguridad: Cómo funciona HMAC-SHA256

1. **Wompi envía el webhook** con:
   - Body: JSON de la transacción
   - Header `X-Signature`: HMAC-SHA256(body, WOMPI_EVENTS_SECRET)

2. **Nuestro código verifica:**
   - Calcula el HMAC esperado usando WOMPI_EVENTS_SECRET
   - Compara con el signature recibido
   - Si no coincide → rechaza (403)

3. **Esto garantiza:**
   - ✅ El webhook viene realmente de Wompi
   - ✅ El webhook no fue modificado en tránsito
   - ✅ Seguridad contra ataques MITM

---

## 🚀 Variables de Entorno Necesarias

En Railway, asegúrate de tener:

```
WOMPI_PUBLIC_KEY=pub_test_XXXXXX
WOMPI_PRIVATE_KEY=prv_test_XXXXXX
WOMPI_EVENTS_SECRET=test_events_XXXXXX
```

Estas las proporciona Wompi en el dashboard.

---

## 📞 Si sigue sin funcionar

1. **Revisa los logs de Railway:**
   - Busca "Firma de Wompi verificada" → ✅ funciona
   - Busca "Firma de Wompi inválida" → ❌ problema de configuración

2. **Verifica en Wompi:**
   - ¿El webhook está activo? (check verde)
   - ¿La URL es correcta?
   - ¿Wompi está enviando requests? (historial de eventos)

3. **Test local:**
   ```bash
   python manage.py runserver
   # Simula un webhook de Wompi con curl
   curl -X POST http://localhost:8000/api/webhooks/wompi/ \
     -H "Content-Type: application/json" \
     -H "X-Signature: test_signature" \
     -d '{"event":"transaction.updated","data":{"transaction":{"id":"txn_123","reference":"REF-123","status":"APPROVED"}}}'
   ```

---

## 📝 Cambios realizados (Commit)

```
commit 233675b
Author: Sistema de pago
Date: 2026-06-20

fix: Implementar verificación correcta de firma (signature) en webhook de Wompi

- Añadir función _verify_signature() con HMAC-SHA256
- Verificar header X-Signature requerido por Wompi
- Mejorar logging para debugging
- Rechazar webhooks sin firma válida (403)
- Mejorar manejo de status APPROVED/DECLINED
```

---

## ✨ Próximos pasos

1. ✅ Deploy a Railway (ya está hecho)
2. ⚠️ Configura el webhook en dashboard de Wompi
3. 🧪 Haz un pago de prueba
4. 📊 Verifica que el status cambia a "PROGRAMADA" automáticamente

¡El sistema de pago debería funcionar correctamente ahora! 🎉
