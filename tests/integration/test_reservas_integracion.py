"""
Pruebas de Integración - Flujo de Reservas y Facturación.

Verifica la persistencia de reservas y la emisión de señales en la base de datos,
así como la interacción con vistas a través del cliente HTTP.
"""
import pytest
import datetime
from django.urls import reverse
from usuarios.models import CustomUser
from canchas.models import Cancha, Deporte, Disponibilidad
from negocio.models import Reserva, Factura

@pytest.mark.django_db
class TestFlujoReservasIntegracion:
    """Pruebas End-to-End para reservas de canchas y facturación automática."""

    @pytest.fixture
    def setup_cancha(self):
        """Prepara el entorno de datos relacionales."""
        dueno = CustomUser.objects.create_user(
            username='dueño_reserva',
            email='dueño@test.com',
            password='Password123*',
            rol='DUEÑO'
        )
        deportista = CustomUser.objects.create_user(
            username='jugador1',
            email='jugador1@test.com',
            password='Password123*',
            rol='DEPORTISTA'
        )
        deporte = Deporte.objects.create(nombre='Fútbol 5')
        cancha = Cancha.objects.create(
            dueño=dueno,
            nombre='Cancha Sintética Norte',
            descripcion='Cancha cubierta',
            precio=80000.00,
            ubicacion='Av 1 # 2-3',
            deporte=deporte
        )
        # Disponibilidad para un lunes de 10:00 a 12:00
        Disponibilidad.objects.create(
            cancha=cancha,
            dia_semana=0,  # 0 = Lunes
            hora_inicio=datetime.time(10, 0),
            hora_fin=datetime.time(12, 0)
        )
        return {
            'cancha': cancha,
            'jugador': deportista
        }

    def test_creacion_reserva_persiste_y_genera_factura(self, setup_cancha):
        """
        # Arrange
        Se utiliza la fixture `setup_cancha` que inserta un Deporte, Cancha, 
        Disponibilidad y un usuario Deportista en la base de datos real de pruebas.
        """
        cancha = setup_cancha['cancha']
        jugador = setup_cancha['jugador']
        
        # Fecha de reserva para un lunes (2026-06-15 es lunes)
        fecha_reserva = datetime.date(2026, 6, 15)
        hora_reserva = datetime.time(10, 0)

        """
        # Act
        El sistema crea la Reserva utilizando el ORM, lo que dispara las señales
        (signals) conectadas al ciclo de vida del modelo (post_save).
        """
        reserva = Reserva.objects.create(
            cancha=cancha,
            usuario=jugador,
            fecha=fecha_reserva,
            hora=hora_reserva
        )

        """
        # Assert
        Comprobamos persistencia y la cascada relacional (generación de factura).
        """
        assert Reserva.objects.count() == 1
        reserva_db = Reserva.objects.get(id=reserva.id)
        assert reserva_db.estado == 'PROGRAMADA'
        assert reserva_db.pagado is False

        # Verificación crítica: La señal de `post_save` debió crear una Factura automáticamente.
        assert Factura.objects.filter(reserva=reserva_db).exists()
        factura_db = Factura.objects.get(reserva=reserva_db)
        
        # El precio de la factura debe coincidir con el precio de la cancha
        assert factura_db.total == 80000.00
        # Referencia de pago fue auto-generada
        assert factura_db.referencia_pago is not None

    def test_cancelacion_reserva_http_flow(self, app_cliente, setup_cancha):
        """
        # Arrange
        Creamos una reserva en BD y autenticamos al cliente HTTP.
        """
        cancha = setup_cancha['cancha']
        jugador = setup_cancha['jugador']
        
        # Iniciar sesión
        app_cliente.force_login(jugador)
        
        # Reserva para una fecha futura
        fecha_reserva = datetime.date(2026, 8, 15)
        reserva = Reserva.objects.create(
            cancha=cancha,
            usuario=jugador,
            fecha=fecha_reserva,
            hora=datetime.time(11, 0)
        )
        
        url_cancelar = reverse('negocio:cancelar_reserva', kwargs={'reserva_id': reserva.id})

        """
        # Act
        Enviamos un POST HTTP simulando al usuario cancelando desde la interfaz.
        """
        respuesta = app_cliente.post(url_cancelar)

        """
        # Assert
        Verificamos redirección y el cambio de estado en la base de datos real.
        """
        assert respuesta.status_code == 302 # Redirección tras éxito
        
        reserva.refresh_from_db()
        assert reserva.estado == 'CANCELADA'
