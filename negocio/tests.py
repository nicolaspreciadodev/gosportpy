# negocio/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from usuarios.models import CustomUser
from canchas.models import Cancha, Deporte
from negocio.models import Reserva, Factura
import datetime


class FacturaDetalleViewTest(TestCase):
    """Tests de integración para la vista FacturaDetalleView."""

    def setUp(self):
        self.client = Client()
        self.deporte = Deporte.objects.create(nombre='Fútbol')

        self.dueño = CustomUser.objects.create_user(
            username='dueño1', password='pass123', rol='DUEÑO'
        )
        self.deportista = CustomUser.objects.create_user(
            username='deportista1', password='pass123', rol='DEPORTISTA'
        )
        self.otro_deportista = CustomUser.objects.create_user(
            username='deportista2', password='pass123', rol='DEPORTISTA'
        )
        self.cancha = Cancha.objects.create(
            nombre='Cancha Test', precio=80.00,
            ubicacion='Centro', dueño=self.dueño, deporte=self.deporte
        )
        # La señal crea la Factura automáticamente al guardar la Reserva
        self.reserva = Reserva.objects.create(
            usuario=self.deportista, cancha=self.cancha,
            fecha=datetime.date(2026, 6, 15), hora=datetime.time(10, 0)
        )
        self.factura = self.reserva.factura

    def test_propietario_puede_ver_factura(self):
        """El deportista dueño de la reserva accede correctamente."""
        self.client.login(username='deportista1', password='pass123')
        url = reverse('negocio:factura_detalle', args=[self.factura.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.factura.total))

    def test_otro_usuario_no_puede_ver_factura(self):
        """Un deportista ajeno es redirigido al dashboard. Edge case: acceso cruzado."""
        self.client.login(username='deportista2', password='pass123')
        url = reverse('negocio:factura_detalle', args=[self.factura.id])
        response = self.client.get(url)
        self.assertRedirects(response, reverse('dashboard'))

    def test_usuario_no_autenticado_redirige_a_login(self):
        """Edge case: acceso sin autenticación."""
        url = reverse('negocio:factura_detalle', args=[self.factura.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_factura_inexistente_retorna_404(self):
        """Edge case: ID de factura que no existe."""
        self.client.login(username='deportista1', password='pass123')
        url = reverse('negocio:factura_detalle', args=[9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class DashboardRolTest(TestCase):
    """Verifica que el dashboard renderiza el bloque correcto según el rol."""

    def setUp(self):
        self.client = Client()
        self.dueño = CustomUser.objects.create_user(
            username='dueño2', password='pass123', rol='DUEÑO'
        )
        self.deportista = CustomUser.objects.create_user(
            username='dep2', password='pass123', rol='DEPORTISTA'
        )

    def test_dueño_ve_seccion_mis_canchas(self):
        self.client.login(username='dueño2', password='pass123')
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'Mis Canchas')

    def test_deportista_ve_seccion_canchas_disponibles(self):
        self.client.login(username='dep2', password='pass123')
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'Canchas Cerca de Ti')
