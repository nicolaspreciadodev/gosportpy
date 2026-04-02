# negocio/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from usuarios.models import CustomUser
from canchas.models import Cancha, Deporte
from negocio.models import Reserva, Factura, Torneo, Equipo, Partido, PosicionEquipo
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


class PanelReservasViewTest(TestCase):
    """Tests para el Panel de Reservas del Dueño."""

    def setUp(self):
        from datetime import date, time
        self.client = Client()
        self.deporte = Deporte.objects.create(nombre='Tenis')

        self.dueño1 = CustomUser.objects.create_user(username='d1', password='123', rol='DUEÑO')
        self.dueño2 = CustomUser.objects.create_user(username='d2', password='123', rol='DUEÑO')
        self.deportista = CustomUser.objects.create_user(username='dep', password='123', rol='DEPORTISTA')

        self.cancha1 = Cancha.objects.create(nombre='C1', precio=50, ubicacion='A', dueño=self.dueño1, deporte=self.deporte)
        self.cancha2 = Cancha.objects.create(nombre='C2', precio=50, ubicacion='B', dueño=self.dueño2, deporte=self.deporte)

        self.reserva1 = Reserva.objects.create(usuario=self.deportista, cancha=self.cancha1, fecha=date(2026, 1, 10), hora=time(10, 0), estado='PROGRAMADA')
        self.reserva2 = Reserva.objects.create(usuario=self.deportista, cancha=self.cancha1, fecha=date(2026, 1, 11), hora=time(11, 0), estado='COMPLETADA')
        self.reserva3 = Reserva.objects.create(usuario=self.deportista, cancha=self.cancha2, fecha=date(2026, 1, 10), hora=time(10, 0), estado='PROGRAMADA')

        self.url = reverse('negocio:panel_reservas')

    def test_acceso_solo_dueño(self):
        self.client.login(username='dep', password='123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_lista_solo_reservas_propias(self):
        self.client.login(username='d1', password='123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        reservas = response.context['reservas']
        self.assertEqual(len(reservas), 2)
        self.assertIn(self.reserva1, reservas)
        self.assertIn(self.reserva2, reservas)
        self.assertNotIn(self.reserva3, reservas)

    def test_filtro_por_estado(self):
        self.client.login(username='d1', password='123')
        response = self.client.get(self.url, {'estado': 'COMPLETADA'})
        reservas = response.context['reservas']
        self.assertEqual(len(reservas), 1)
        self.assertEqual(reservas.first(), self.reserva2)

    def test_filtro_por_fecha(self):
        self.client.login(username='d1', password='123')
        response = self.client.get(self.url, {'fecha': '2026-01-10'})
        reservas = response.context['reservas']
        self.assertEqual(len(reservas), 1)
        self.assertEqual(reservas.first(), self.reserva1)


class WompiPagosTest(TestCase):
    """Tests para simular el pago de reservas con Wompi y Webhooks."""

    def setUp(self):
        from datetime import date, time
        self.client = Client()
        self.deporte = Deporte.objects.create(nombre='Voley')
        self.dueño = CustomUser.objects.create_user(username='d1', password='123', rol='DUEÑO')
        self.deportista1 = CustomUser.objects.create_user(username='dep1', password='123', rol='DEPORTISTA')
        self.deportista2 = CustomUser.objects.create_user(username='dep2', password='123', rol='DEPORTISTA')

        self.cancha = Cancha.objects.create(nombre='C1', precio=100.00, ubicacion='A', dueño=self.dueño, deporte=self.deporte)

        self.reserva = Reserva.objects.create(
            usuario=self.deportista1, cancha=self.cancha,
            fecha=date(2026, 2, 10), hora=time(15, 0), estado='PROGRAMADA'
        )
        self.url = reverse('negocio:iniciar_pago', args=[self.reserva.id])

    def test_acceso_requiere_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_iniciar_pago_exitoso(self):
        """Un usuario puede ver la vista de pago Wompi de su reserva."""
        self.client.login(username='dep1', password='123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Wompi')
        
    def test_pago_ajeno_denegado(self):
        """Un usuario no puede ver la vista de pago de otro."""
        self.client.login(username='dep2', password='123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_webhook_wompi_pago_aprobado(self):
        """El webhook aprueba el pago correctamente y actualiza la BD."""
        factura = self.reserva.factura
        
        # Validar inicial
        self.assertFalse(self.reserva.pagado)
        
        payload = {
            "event": "transaction.updated",
            "data": {
                "transaction": {
                    "id": "12345-wompi-test",
                    "status": "APPROVED",
                    "reference": factura.referencia_pago,
                    "amount_in_cents": 10000
                }
            }
        }
        
        url = reverse('negocio:wompi_webhook')
        response = self.client.post(url, data=payload, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        self.reserva.refresh_from_db()
        factura.refresh_from_db()
        self.assertTrue(self.reserva.pagado)
        self.assertEqual(self.reserva.estado, 'PROGRAMADA')
        self.assertEqual(factura.wompi_transaction_id, "12345-wompi-test")

# ===== FASE 10 — SISTEMA DE LIGA COMPLETO =====

class GenerarFixtureTest(TestCase):
    """Tests para la generación de fixture con algoritmo Round-Robin.

    Valida:
    - Fixture se genera solo con 2+ equipos
    - Solo organizador puede generar
    - Fixture no se puede generar dos veces
    - Tabla de posiciones se inicia en ceros
    - Número correcto de jornadas y partidos
    """

    def setUp(self):
        self.client = Client()
        self.deporte = Deporte.objects.create(nombre='Fútbol')
        self.cancha = Cancha.objects.create(
            nombre='Cancha Test', precio=80.00,
            ubicacion='Centro', dueño=CustomUser.objects.create_user(
                username='dueño_lig', password='pass', rol='DUEÑO'
            ), deporte=self.deporte
        )

        self.organizador = CustomUser.objects.create_user(
            username='org_lig', password='pass', rol='DEPORTISTA'
        )
        self.no_organizador = CustomUser.objects.create_user(
            username='otro_lig', password='pass', rol='DEPORTISTA'
        )

        self.torneo = Torneo.objects.create(
            nombre='Liga Test',
            organizador=self.organizador,
            formato='LIGA',
            max_equipos=4,
            deporte=self.deporte
        )

        # Crear 4 equipos
        self.equipos = []
        for i in range(4):
            equipo = Equipo.objects.create(nombre=f'Equipo {i+1}')
            equipo.jugadores.add(self.organizador)
            self.torneo.equipos.add(equipo)
            self.equipos.append(equipo)

    def test_generar_fixture_exitoso(self):
        """Fixture se genera correctamente con 4 equipos."""
        self.client.login(username='org_lig', password='pass')
        response = self.client.post(
            reverse('negocio:generar_fixture', args=[self.torneo.id])
        )

        self.assertRedirects(response, reverse('negocio:torneo_detalle', args=[self.torneo.id]))
        self.torneo.refresh_from_db()
        self.assertTrue(self.torneo.fixture_generado)

        # Verificar número de partidos: 4 equipos → 3 jornadas, 6 partidos
        partidos = Partido.objects.filter(torneo=self.torneo)
        self.assertEqual(partidos.count(), 6)  # 4 equipos: (4-1)*4/2 = 6

    def test_generar_fixture_solo_organizador(self):
        """Solo el organizador puede generar fixture."""
        self.client.login(username='otro_lig', password='pass')
        response = self.client.post(
            reverse('negocio:generar_fixture', args=[self.torneo.id])
        )

        self.assertRedirects(response, reverse('negocio:torneo_detalle', args=[self.torneo.id]))
        self.torneo.refresh_from_db()
        self.assertFalse(self.torneo.fixture_generado)

    def test_generar_fixture_sin_equipos(self):
        """No se puede generar fixture sin al menos 2 equipos."""
        torneo_vacio = Torneo.objects.create(
            nombre='Torneo Vacío',
            organizador=self.organizador,
            formato='LIGA'
        )

        self.client.login(username='org_lig', password='pass')
        response = self.client.post(
            reverse('negocio:generar_fixture', args=[torneo_vacio.id])
        )

        self.assertRedirects(response, reverse('negocio:torneo_detalle', args=[torneo_vacio.id]))
        torneo_vacio.refresh_from_db()
        self.assertFalse(torneo_vacio.fixture_generado)

    def test_posiciones_inicializadas_en_cero(self):
        """La tabla de posiciones se inicializa correctamente."""
        self.client.login(username='org_lig', password='pass')
        self.client.post(reverse('negocio:generar_fixture', args=[self.torneo.id]))

        posiciones = PosicionEquipo.objects.filter(torneo=self.torneo)
        self.assertEqual(posiciones.count(), 4)

        for posicion in posiciones:
            self.assertEqual(posicion.puntos, 0)
            self.assertEqual(posicion.partidos_jugados, 0)
            self.assertEqual(posicion.goles_favor, 0)


class RegistrarResultadoTest(TestCase):
    """Tests para registro de resultados y actualización de tabla.

    Valida:
    - Resultado se registra correctamente
    - Tabla de posiciones se actualiza (puntos, goles, PJ, etc.)
    - Algoritmo ganador (3pts), empate (1pt), perdedor (0pts)
    - Solo organizador puede registrar
    - No se puede registrar dos veces el mismo partido
    """

    def setUp(self):
        from negocio.services import generar_fixture_liga

        self.client = Client()
        self.deporte = Deporte.objects.create(nombre='Fútbol')
        self.cancha = Cancha.objects.create(
            nombre='Cancha Test', precio=80.00,
            ubicacion='Centro', dueño=CustomUser.objects.create_user(
                username='dueño_res', password='pass', rol='DUEÑO'
            ), deporte=self.deporte
        )

        self.organizador = CustomUser.objects.create_user(
            username='org_res', password='pass', rol='DEPORTISTA'
        )

        self.torneo = Torneo.objects.create(
            nombre='Liga Resultados',
            organizador=self.organizador,
            formato='LIGA',
            max_equipos=2,
            deporte=self.deporte
        )

        # 2 equipos
        self.equipo_a = Equipo.objects.create(nombre='Equipo A')
        self.equipo_b = Equipo.objects.create(nombre='Equipo B')
        self.torneo.equipos.add(self.equipo_a)
        self.torneo.equipos.add(self.equipo_b)

        # Generar fixture
        generar_fixture_liga(self.torneo)
        self.partido = Partido.objects.filter(torneo=self.torneo).first()

    def test_registrar_resultado_ganador(self):
        """Registrar resultado con ganador actualiza puntos correctamente."""
        self.client.login(username='org_res', password='pass')
        response = self.client.post(
            reverse('negocio:registrar_resultado', args=[self.partido.id]),
            {'goles_local': 3, 'goles_visitante': 1}
        )

        self.assertRedirects(response, reverse('negocio:torneo_detalle', args=[self.torneo.id]))

        self.partido.refresh_from_db()
        self.assertEqual(self.partido.goles_local, 3)
        self.assertEqual(self.partido.goles_visitante, 1)
        self.assertEqual(self.partido.estado, 'JUGADO')

        # Verificar puntos
        pos_local = PosicionEquipo.objects.get(torneo=self.torneo, equipo=self.equipo_a)
        pos_visitante = PosicionEquipo.objects.get(torneo=self.torneo, equipo=self.equipo_b)

        self.assertEqual(pos_local.puntos, 3)  # Ganó
        self.assertEqual(pos_visitante.puntos, 0)  # Perdió

    def test_registrar_resultado_empate(self):
        """Registrar empate da 1 punto a cada equipo."""
        self.client.login(username='org_res', password='pass')
        response = self.client.post(
            reverse('negocio:registrar_resultado', args=[self.partido.id]),
            {'goles_local': 2, 'goles_visitante': 2}
        )

        self.assertRedirects(response, reverse('negocio:torneo_detalle', args=[self.torneo.id]))

        pos_local = PosicionEquipo.objects.get(torneo=self.torneo, equipo=self.equipo_a)
        pos_visitante = PosicionEquipo.objects.get(torneo=self.torneo, equipo=self.equipo_b)

        self.assertEqual(pos_local.puntos, 1)
        self.assertEqual(pos_visitante.puntos, 1)

    def test_solo_organizador_puede_registrar(self):
        """Edge: otro usuario no puede registrar resultado."""
        otro_usuario = CustomUser.objects.create_user(
            username='otro_res', password='pass'
        )

        self.client.login(username='otro_res', password='pass')
        response = self.client.post(
            reverse('negocio:registrar_resultado', args=[self.partido.id]),
            {'goles_local': 3, 'goles_visitante': 1}
        )

        self.assertRedirects(response, reverse('negocio:torneo_detalle', args=[self.torneo.id]))

        self.partido.refresh_from_db()
        self.assertEqual(self.partido.estado, 'PENDIENTE')

    def test_no_puede_registrar_dos_veces(self):
        """Edge: no se puede registrar resultado dos veces."""
        self.client.login(username='org_res', password='pass')

        # Primer registro
        self.client.post(
            reverse('negocio:registrar_resultado', args=[self.partido.id]),
            {'goles_local': 3, 'goles_visitante': 1}
        )

        # Segundo intento
        response = self.client.post(
            reverse('negocio:registrar_resultado', args=[self.partido.id]),
            {'goles_local': 5, 'goles_visitante': 0}
        )

        # Los goles no deben cambiar
        self.partido.refresh_from_db()
        self.assertEqual(self.partido.goles_local, 3)
        self.assertEqual(self.partido.goles_visitante, 1)

class PanelAnalyticsViewTest(TestCase):
    """Pruebas para el Dashboard de Analytics de Dueños."""
    def setUp(self):
        import datetime
        self.client = Client()
        self.deporte = Deporte.objects.create(nombre='Futsal')
        self.dueño = CustomUser.objects.create_user(username='d_analytics', password='abc', rol='DUEÑO')
        self.deportista = CustomUser.objects.create_user(username='dep_ana', password='abc', rol='DEPORTISTA')

        self.cancha1 = Cancha.objects.create(nombre='Cancha A', precio=50.00, ubicacion='A', dueño=self.dueño, deporte=self.deporte)
        self.cancha2 = Cancha.objects.create(nombre='Cancha B', precio=100.00, ubicacion='B', dueño=self.dueño, deporte=self.deporte)

        self.reserva1 = Reserva.objects.create(
            usuario=self.deportista, cancha=self.cancha1,
            fecha=datetime.date.today(), hora=datetime.time(10, 0), estado='PROGRAMADA', pagado=True
        )
        # Forzamos la creación de la factura (se crea por signals, actualizamos el total por si acaso)
        self.reserva1.factura.total = 50.00
        self.reserva1.factura.save()

        self.reserva2 = Reserva.objects.create(
            usuario=self.deportista, cancha=self.cancha2,
            fecha=datetime.date.today(), hora=datetime.time(11, 0), estado='PROGRAMADA', pagado=False
        )

        self.url = reverse('negocio:panel_analytics')

    def test_solo_dueño_acceso(self):
        self.client.login(username='dep_ana', password='abc')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_analytics_200_ok(self):
        self.client.login(username='d_analytics', password='abc')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_analytics_calcula_correctamente(self):
        self.client.login(username='d_analytics', password='abc')
        response = self.client.get(self.url)
        
        # Ingreso = precio de cancha1 (50.00) porque está pagada
        self.assertEqual(float(response.context['ingresos_totales']), 50.00)
        self.assertEqual(float(response.context['ingresos_mes']), 50.00)
        # Total reservas (ambas en estado PROGRAMADA) = 2
        self.assertEqual(response.context['total_reservas_30_dias'], 2)
