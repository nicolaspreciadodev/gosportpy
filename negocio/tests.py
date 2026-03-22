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

class CancelarReservaViewTest(TestCase):
    """Tests para la vista de CancelarReservaView."""

    def setUp(self):
        from datetime import timedelta
        from django.utils import timezone
        
        self.client = Client()
        self.deporte = Deporte.objects.create(nombre='Fútbol')

        self.dueño = CustomUser.objects.create_user(
            username='dueño_cx', password='pass', rol='DUEÑO'
        )
        self.deportista = CustomUser.objects.create_user(
            username='dep_cx', password='pass', rol='DEPORTISTA'
        )
        self.cancha = Cancha.objects.create(
            nombre='Cancha Test CX', precio=80.00,
            ubicacion='Centro', dueño=self.dueño, deporte=self.deporte
        )
        
        # Una reserva a 3 días (puede cancelar)
        future_dt = timezone.now() + timedelta(days=3)
        self.reserva_lejos = Reserva.objects.create(
            usuario=self.deportista, cancha=self.cancha,
            fecha=future_dt.date(), hora=future_dt.time(), estado='PROGRAMADA'
        )

        # Una reserva a 2 horas (NO puede cancelar)
        close_dt = timezone.now() + timedelta(hours=2)
        self.reserva_cerca = Reserva.objects.create(
            usuario=self.deportista, cancha=self.cancha,
            fecha=close_dt.date(), hora=close_dt.time(), estado='PROGRAMADA'
        )

    def test_cancelacion_exitosa(self):
        """Si falta más de 24h, se puede cancelar."""
        self.client.login(username='dep_cx', password='pass')
        url = reverse('negocio:cancelar_reserva', args=[self.reserva_lejos.id])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('dashboard'))
        self.reserva_lejos.refresh_from_db()
        self.assertEqual(self.reserva_lejos.estado, 'CANCELADA')

    def test_cancelacion_fuera_de_tiempo(self):
        """Si falta menos de 24h, NO se puede cancelar y muestra error."""
        self.client.login(username='dep_cx', password='pass')
        url = reverse('negocio:cancelar_reserva', args=[self.reserva_cerca.id])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('dashboard'))
        self.reserva_cerca.refresh_from_db()
        self.assertEqual(self.reserva_cerca.estado, 'PROGRAMADA')

class InscribirEquipoViewTest(TestCase):
    """Tests para la inscripción de un equipo a un torneo."""

    def setUp(self):
        from datetime import date
        from negocio.models import Torneo, Equipo
        
        self.client = Client()
        self.deporte = Deporte.objects.create(nombre='Basketball')

        self.dueño = CustomUser.objects.create_user(
            username='org_torneo', password='123', rol='DUEÑO'
        )
        self.deportista1 = CustomUser.objects.create_user(
            username='jugador1', password='123', rol='DEPORTISTA'
        )
        self.deportista2 = CustomUser.objects.create_user(
            username='jugador2', password='123', rol='DEPORTISTA'
        )
        
        self.torneo = Torneo.objects.create(
            nombre='Copa Primavera',
            estado='PUBLICADO',
            organizador=self.dueño,
            deporte=self.deporte,
            fecha_inicio=date(2026, 9, 10),
            fecha_fin=date(2026, 9, 20)
        )

        self.torneo_cerrado = Torneo.objects.create(
            nombre='Copa Invierno',
            estado='PENDIENTE',
            organizador=self.dueño,
            deporte=self.deporte
        )

        self.equipo = Equipo.objects.create(nombre='Los Tigres')
        self.equipo.jugadores.add(self.deportista1)

    def test_inscripcion_exitosa(self):
        """Un jugador del equipo puede inscribirlo si el torneo está publicado."""
        self.client.login(username='jugador1', password='123')
        url = reverse('negocio:inscribir_torneo', args=[self.torneo.id])
        response = self.client.post(url, {'equipo_id': self.equipo.id})
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(self.equipo.torneos.filter(id=self.torneo.id).exists())

    def test_inscripcion_fallida_no_pertenece_equipo(self):
        """Si un usuario no pertenece al equipo, no puede inscribirlo."""
        self.client.login(username='jugador2', password='123')
        url = reverse('negocio:inscribir_torneo', args=[self.torneo.id])
        response = self.client.post(url, {'equipo_id': self.equipo.id})
        self.assertRedirects(response, reverse('dashboard'))
        self.assertFalse(self.equipo.torneos.filter(id=self.torneo.id).exists())

    def test_inscripcion_fallida_torneo_no_publicado(self):
        """Falla si el torneo no está en estado PUBLICADO."""
        self.client.login(username='jugador1', password='123')
        url = reverse('negocio:inscribir_torneo', args=[self.torneo_cerrado.id])
        response = self.client.post(url, {'equipo_id': self.equipo.id})
        self.assertRedirects(response, reverse('dashboard'))
        self.assertFalse(self.equipo.torneos.filter(id=self.torneo_cerrado.id).exists())
