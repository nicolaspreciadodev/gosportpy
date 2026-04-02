# canchas/tests.py
"""
Tests de integración para el CRUD de canchas.

Cubre: permisos por rol, validaciones de formulario, edge cases.
"""
from django.test import TestCase, Client
from django.urls import reverse
from usuarios.models import CustomUser
from canchas.models import Cancha, Deporte


class CanchaBaseTestCase(TestCase):
    """Fixtures compartidos entre todos los tests de canchas."""

    def setUp(self):
        self.client = Client()
        self.deporte = Deporte.objects.create(nombre='Fútbol')

        self.dueño = CustomUser.objects.create_user(
            username='dueño_test', password='pass123', rol='DUEÑO'
        )
        self.otro_dueño = CustomUser.objects.create_user(
            username='dueño_otro', password='pass123', rol='DUEÑO'
        )
        self.deportista = CustomUser.objects.create_user(
            username='deportista_test', password='pass123', rol='DEPORTISTA'
        )
        self.cancha = Cancha.objects.create(
            nombre='Cancha Central', precio=80.00,
            ubicacion='Zona Norte', dueño=self.dueño, deporte=self.deporte
        )


class CanchaListViewTest(CanchaBaseTestCase):

    def test_lista_accesible_para_deportista(self):
        self.client.login(username='deportista_test', password='pass123')
        response = self.client.get(reverse('canchas:lista'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cancha Central')

    def test_filtro_por_deporte_funciona(self):
        self.client.login(username='deportista_test', password='pass123')
        response = self.client.get(reverse('canchas:lista'), {'deporte': self.deporte.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cancha Central')

    def test_filtro_deporte_inexistente_retorna_lista_vacia(self):
        """Edge case: deporte_id que no existe no debe crashear."""
        self.client.login(username='deportista_test', password='pass123')
        response = self.client.get(reverse('canchas:lista'), {'deporte': 9999})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Cancha Central')


class CanchaCreateViewTest(CanchaBaseTestCase):

    def _datos_validos(self):
        return {
            'nombre': 'Nueva Cancha', 'precio': '60.00',
            'ubicacion': 'Sur', 'deporte': self.deporte.id, 'descripcion': ''
        }

    def test_dueño_puede_crear_cancha(self):
        self.client.login(username='dueño_test', password='pass123')
        response = self.client.post(reverse('canchas:nueva'), self._datos_validos())
        self.assertEqual(Cancha.objects.count(), 2)
        self.assertEqual(response.status_code, 302)

    def test_deportista_no_puede_acceder_a_crear(self):
        """Edge case: rol incorrecto → 403."""
        self.client.login(username='deportista_test', password='pass123')
        response = self.client.get(reverse('canchas:nueva'))
        self.assertEqual(response.status_code, 403)

    def test_precio_negativo_falla_validacion(self):
        """Edge case: precio inválido no debe persistir."""
        self.client.login(username='dueño_test', password='pass123')
        datos = self._datos_validos()
        datos['precio'] = '-50'
        response = self.client.post(reverse('canchas:nueva'), datos)
        self.assertEqual(Cancha.objects.count(), 1)
        self.assertContains(response, 'mayor a cero')

    def test_precio_cero_falla_validacion(self):
        """Edge case: precio = 0 no es válido."""
        self.client.login(username='dueño_test', password='pass123')
        datos = self._datos_validos()
        datos['precio'] = '0'
        response = self.client.post(reverse('canchas:nueva'), datos)
        self.assertEqual(Cancha.objects.count(), 1)

    def test_precio_excesivo_falla_validacion(self):
        """Edge case: precio > 1,000,000."""
        self.client.login(username='dueño_test', password='pass123')
        datos = self._datos_validos()
        datos['precio'] = '9999999'
        response = self.client.post(reverse('canchas:nueva'), datos)
        self.assertEqual(Cancha.objects.count(), 1)


class CanchaUpdateViewTest(CanchaBaseTestCase):

    def test_dueño_puede_editar_su_cancha(self):
        self.client.login(username='dueño_test', password='pass123')
        response = self.client.post(
            reverse('canchas:editar', args=[self.cancha.pk]),
            {'nombre': 'Cancha Editada', 'precio': '90.00',
             'ubicacion': 'Norte', 'deporte': self.deporte.id, 'descripcion': ''}
        )
        self.cancha.refresh_from_db()
        self.assertEqual(self.cancha.nombre, 'Cancha Editada')

    def test_otro_dueño_no_puede_editar_cancha_ajena(self):
        """Edge case: propiedad cruzada → 403."""
        self.client.login(username='dueño_otro', password='pass123')
        response = self.client.get(reverse('canchas:editar', args=[self.cancha.pk]))
        self.assertEqual(response.status_code, 403)


class CanchaDeleteViewTest(CanchaBaseTestCase):

    def test_dueño_puede_eliminar_su_cancha(self):
        self.client.login(username='dueño_test', password='pass123')
        self.client.post(reverse('canchas:eliminar', args=[self.cancha.pk]))
        self.assertEqual(Cancha.objects.count(), 0)

    def test_otro_dueño_no_puede_eliminar_cancha_ajena(self):
        """Edge case crítico: nunca debe eliminar datos de otro usuario."""
        self.client.login(username='dueño_otro', password='pass123')
        response = self.client.post(reverse('canchas:eliminar', args=[self.cancha.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Cancha.objects.count(), 1)


import datetime
from .models import Disponibilidad
from negocio.models import Reserva

class DisponibilidadTests(CanchaBaseTestCase):
    def setUp(self):
        super().setUp()
        self.disp1 = Disponibilidad.objects.create(
            cancha=self.cancha,
            dia_semana=0, # Lunes
            hora_inicio=datetime.time(10, 0),
            hora_fin=datetime.time(14, 0)
        )
        self.lunes_fecha = '2023-10-02' # 2023-10-02 es un Lunes

    # Service Tests
    def test_generar_slots(self):
        from .services import _generar_slots_por_hora
        slots = _generar_slots_por_hora(datetime.time(10, 0), datetime.time(12, 0))
        self.assertEqual(len(slots), 2)
        self.assertEqual(slots[0], datetime.time(10, 0))

    def test_obtener_slots_sin_reservas(self):
        from .services import obtener_slots_disponibles
        slots = obtener_slots_disponibles(self.cancha.id, self.lunes_fecha)
        self.assertEqual(len(slots), 4) # 10, 11, 12, 13

    def test_obtener_slots_con_reserva(self):
        Reserva.objects.create(
            usuario=self.deportista,
            cancha=self.cancha,
            fecha=self.lunes_fecha,
            hora=datetime.time(11, 0)
        )
        from .services import obtener_slots_disponibles
        slots = obtener_slots_disponibles(self.cancha.id, self.lunes_fecha)
        self.assertEqual(len(slots), 3)
        self.assertNotIn(datetime.time(11, 0), slots)

    def test_validar_slot_disponible(self):
        from .services import validar_slot_disponible
        self.assertTrue(validar_slot_disponible(self.cancha.id, self.lunes_fecha, datetime.time(10,0)))
        self.assertFalse(validar_slot_disponible(self.cancha.id, self.lunes_fecha, datetime.time(15,0)))

    # API View Tests
    def test_slots_api_falta_fecha(self):
        res = self.client.get(reverse('canchas:slots', args=[self.cancha.id]))
        self.assertEqual(res.status_code, 400)

    def test_slots_api_success(self):
        res = self.client.get(reverse('canchas:slots', args=[self.cancha.id]), {'fecha': self.lunes_fecha})
        self.assertEqual(res.status_code, 200)
        self.assertIn('10:00', res.json()['slots'])

    # UI View Tests
    def test_dueño_puede_ver_gestionar_disponibilidad(self):
        self.client.login(username='dueño_test', password='pass123')
        res = self.client.get(reverse('canchas:disponibilidad', args=[self.cancha.id]))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '10:00')

    def test_dueño_puede_agregar_disponibilidad(self):
        self.client.login(username='dueño_test', password='pass123')
        res = self.client.post(reverse('canchas:disponibilidad', args=[self.cancha.id]), {
            'dia_semana': 1,
            'hora_inicio': '08:00',
            'hora_fin': '10:00'
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(Disponibilidad.objects.count(), 2)

    def test_dueño_puede_eliminar_disponibilidad(self):
        self.client.login(username='dueño_test', password='pass123')
        res = self.client.post(reverse('canchas:disponibilidad', args=[self.cancha.id]), {
            'delete_id': self.disp1.id
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(Disponibilidad.objects.count(), 0)


# ===== FASE 11: CALIFICACIONES =====

class CalificarCanchaViewTest(CanchaBaseTestCase):
    """Tests para calificación de canchas.

    Valida:
    - Solo si tiene reserva completada
    - Una sola calificación por usuario por cancha
    - Puntuación 1-5
    - Comentario opcional
    """

    def setUp(self):
        super().setUp()
        # Crear una reserva completada para test
        from negocio.models import Reserva
        import datetime

        self.reserva = Reserva.objects.create(
            usuario=self.deportista,
            cancha=self.cancha,
            fecha=datetime.date(2026, 3, 20),
            hora=datetime.time(10, 0),
            estado='COMPLETADA'
        )

    def test_calificar_con_reserva_completada(self):
        """Puede calificar si tiene reserva completada."""
        self.client.login(username='deportista_test', password='pass123')
        response = self.client.post(
            reverse('canchas:calificar', args=[self.cancha.id]),
            {'puntuacion': 5, 'comentario': 'Excelente cancha'}
        )

        self.assertRedirects(response, reverse('canchas:detalle', args=[self.cancha.id]))

        # Verificar que se creó
        from canchas.models import Calificacion
        calificacion = Calificacion.objects.get(usuario=self.deportista, cancha=self.cancha)
        self.assertEqual(calificacion.puntuacion, 5)
        self.assertEqual(calificacion.comentario, 'Excelente cancha')

    def test_no_puede_calificar_sin_reserva(self):
        """Edge: no puede calificar sin haber reservado."""
        otro_deportista = CustomUser.objects.create_user(
            username='otro_dep', password='pass123', rol='DEPORTISTA'
        )

        self.client.login(username='otro_dep', password='pass123')
        response = self.client.post(
            reverse('canchas:calificar', args=[self.cancha.id]),
            {'puntuacion': 5, 'comentario': 'Buen lugar'}
        )

        self.assertRedirects(response, reverse('canchas:detalle', args=[self.cancha.id]))

        from canchas.models import Calificacion
        self.assertEqual(Calificacion.objects.count(), 0)

    def test_no_puede_calificar_dos_veces(self):
        """Edge: no puede calificar la misma cancha dos veces."""
        self.client.login(username='deportista_test', password='pass123')

        # Primera calificación
        self.client.post(
            reverse('canchas:calificar', args=[self.cancha.id]),
            {'puntuacion': 5, 'comentario': 'Primera'}
        )

        # Segundo intento
        response = self.client.post(
            reverse('canchas:calificar', args=[self.cancha.id]),
            {'puntuacion': 3, 'comentario': 'Segunda'}
        )

        self.assertRedirects(response, reverse('canchas:detalle', args=[self.cancha.id]))

        from canchas.models import Calificacion
        # Debe haber solo 1
        self.assertEqual(Calificacion.objects.count(), 1)
        # Con puntuación original
        cal = Calificacion.objects.first()
        self.assertEqual(cal.puntuacion, 5)

    def test_puntuacion_fuera_rango_falla(self):
        """Edge: puntuación debe ser 1-5."""
        self.client.login(username='deportista_test', password='pass123')

        # Puntuación > 5
        response = self.client.post(
            reverse('canchas:calificar', args=[self.cancha.id]),
            {'puntuacion': 10, 'comentario': 'Muy bueno'}
        )

        from canchas.models import Calificacion
        self.assertEqual(Calificacion.objects.count(), 0)

    def test_comentario_opcional(self):
        """Comentario es opcional, solo puntuación es requerida."""
        self.client.login(username='deportista_test', password='pass123')
        response = self.client.post(
            reverse('canchas:calificar', args=[self.cancha.id]),
            {'puntuacion': 4}  # Sin comentario
        )

        self.assertRedirects(response, reverse('canchas:detalle', args=[self.cancha.id]))

        from canchas.models import Calificacion
        cal = Calificacion.objects.get(usuario=self.deportista)
        self.assertEqual(cal.comentario, '')

    def test_no_autenticado_redirige_a_login(self):
        """Edge: usuario no logueado es redirigido."""
        response = self.client.post(
            reverse('canchas:calificar', args=[self.cancha.id]),
            {'puntuacion': 5}
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url.lower())

    def test_promedio_calificacion_calculado(self):
        """Cancha.promedio_calificacion calcula correctamente."""
        from negocio.models import Reserva
        import datetime

        # Crear otra reserva completada para otro usuario
        otro_deportista = CustomUser.objects.create_user(
            username='otro_dep2', password='pass123', rol='DEPORTISTA'
        )
        reserva2 = Reserva.objects.create(
            usuario=otro_deportista,
            cancha=self.cancha,
            fecha=datetime.date(2026, 3, 21),
            hora=datetime.time(11, 0),
            estado='COMPLETADA'
        )

        # Calificar con ambos usuarios
        self.client.login(username='deportista_test', password='pass123')
        self.client.post(
            reverse('canchas:calificar', args=[self.cancha.id]),
            {'puntuacion': 5}
        )

        self.client.logout()
        self.client.login(username='otro_dep2', password='pass123')
        self.client.post(
            reverse('canchas:calificar', args=[self.cancha.id]),
            {'puntuacion': 3}
        )

        # Verificar promedio
        self.cancha.refresh_from_db()
        self.assertEqual(self.cancha.promedio_calificacion, 4.0)
        self.assertEqual(self.cancha.total_calificaciones, 2)


class CanchaFiltrosTest(CanchaBaseTestCase):
    """Tests para la Fase 14 de Búsqueda y Filtros Avanzados."""

    def setUp(self):
        super().setUp()
        self.cancha_sur = Cancha.objects.create(
            nombre='Cancha Sur', precio=120.00,
            ubicacion='Sur', ciudad='Medellín',
            dueño=self.dueño, deporte=self.deporte
        )

    def test_filtro_por_ciudad(self):
        self.client.login(username='deportista_test', password='pass123')
        res = self.client.get(reverse('canchas:lista'), {'ciudad': 'Medellín'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Cancha Sur')
        self.assertNotContains(res, 'Cancha Central') # Default is Bogotá
        
    def test_filtro_por_rango_precio(self):
        self.client.login(username='deportista_test', password='pass123')
        res = self.client.get(reverse('canchas:lista'), {'min_precio': '100', 'max_precio': '150'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Cancha Sur')
        self.assertNotContains(res, 'Cancha Central')

    def test_busqueda_q(self):
        self.client.login(username='deportista_test', password='pass123')
        res = self.client.get(reverse('canchas:lista'), {'q': 'Central'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Cancha Central')
        self.assertNotContains(res, 'Cancha Sur')

