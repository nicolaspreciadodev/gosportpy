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
