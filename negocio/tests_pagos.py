from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
from usuarios.models import CustomUser
from canchas.models import Cancha, Deporte
from negocio.models import Reserva
from django.utils import timezone

class PagoViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dueno = CustomUser.objects.create_user(username='dueno_pagos', email='dueno@pago.com', password='pw', rol='DUEÑO')
        self.deportista = CustomUser.objects.create_user(username='depo_pagos', email='depo@pago.com', password='pw', rol='DEPORTISTA')
        self.deporte = Deporte.objects.create(nombre='Futbol')
        self.cancha = Cancha.objects.create(nombre='Cancha Pago', deporte=self.deporte, precio=55000, dueño=self.dueno)
        
        self.reserva = Reserva.objects.create(
            usuario=self.deportista,
            cancha=self.cancha,
            fecha=timezone.localdate(),
            hora='16:00',
            pagado=False
        )

    @patch('negocio.views.pagos.mercadopago.SDK')
    def test_iniciar_pago_success(self, MockSDK):
        # Configurar el mock para que simule una respuesta exitosa de MP
        mock_preference = MagicMock()
        mock_preference.create.return_value = {
            "status": 201,
            "response": {"id": "mock_pref_12345"}
        }
        
        mock_sdk_instance = MockSDK.return_value
        mock_sdk_instance.preference.return_value = mock_preference
        
        self.client.login(username='depo_pagos', password='pw')
        response = self.client.get(reverse('negocio:iniciar_pago', args=[self.reserva.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'negocio/pagos/checkout.html')
        self.assertEqual(response.context['preference_id'], "mock_pref_12345")

    def test_pago_exitoso_view(self):
        self.client.login(username='depo_pagos', password='pw')
        
        # Simular redirección de MercadoPago exitosa
        url = reverse('negocio:pago_exitoso')
        response = self.client.get(url, {'reserva_id': self.reserva.id, 'payment_id': '9999', 'status': 'approved'})
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'negocio/pagos/pago_exitoso.html')
        
        # Verificar que la reserva se marcó como pagada en BD
        self.reserva.refresh_from_db()
        self.assertTrue(self.reserva.pagado)

    def test_iniciar_pago_ya_pagado(self):
        self.client.login(username='depo_pagos', password='pw')
        self.reserva.pagado = True
        self.reserva.save()
        
        response = self.client.get(reverse('negocio:iniciar_pago', args=[self.reserva.id]))
        # Debe redirigir al dashboard porque ya está pagado
        self.assertRedirects(response, reverse('dashboard'))
