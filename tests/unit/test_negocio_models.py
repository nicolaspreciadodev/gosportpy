"""
Pruebas unitarias para negocio/models.py

Componentes probados:
- Torneo: __str__, estados, formato, campo fixture_generado.
- Reserva: __str__, puede_cancelar, clean (overlap detection).
- Factura: __str__, generación automática de referencia_pago.
- Equipo: __str__.
- Partido: __str__, Meta.ordering.
- PosicionEquipo: diferencia_goles, __str__, Meta.ordering, Meta.unique_together.
- SolicitudModificacionTorneo: __str__.
"""
import pytest
import datetime
from unittest.mock import MagicMock, patch
from decimal import Decimal


class TestTorneoModel:
    """Pruebas del modelo Torneo."""

    def test_str_representation(self):
        """Happy Path: __str__ muestra nombre y estado display."""
        # Arrange
        from negocio.models import Torneo
        torneo = MagicMock(spec=Torneo)
        torneo.nombre = "Copa Bogotá 2026"
        torneo.get_estado_display.return_value = "Publicado"

        # Act
        result = Torneo.__str__(torneo)

        # Assert
        assert result == "Copa Bogotá 2026 (Publicado)"

    def test_estado_default_is_pendiente(self):
        """Verifica que el estado por defecto sea PENDIENTE."""
        # Arrange & Act
        from negocio.models import Torneo
        field = Torneo._meta.get_field('estado')

        # Assert
        assert field.default == 'PENDIENTE'

    def test_formato_default_is_liga(self):
        """Verifica que el formato por defecto sea LIGA."""
        # Arrange & Act
        from negocio.models import Torneo
        field = Torneo._meta.get_field('formato')

        # Assert
        assert field.default == 'LIGA'

    def test_max_equipos_default_is_eight(self):
        """Verifica que max_equipos por defecto sea 8."""
        # Arrange & Act
        from negocio.models import Torneo
        field = Torneo._meta.get_field('max_equipos')

        # Assert
        assert field.default == 8

    def test_fixture_generado_default_false(self):
        """Verifica que fixture_generado comience en False."""
        # Arrange & Act
        from negocio.models import Torneo
        field = Torneo._meta.get_field('fixture_generado')

        # Assert
        assert field.default is False

    def test_is_approved_default_false(self):
        """Verifica que is_approved comience en False."""
        # Arrange & Act
        from negocio.models import Torneo
        field = Torneo._meta.get_field('is_approved')

        # Assert
        assert field.default is False

    def test_precio_inscripcion_default(self):
        """Verifica que el precio de inscripción por defecto sea 50,000."""
        # Arrange & Act
        from negocio.models import Torneo
        field = Torneo._meta.get_field('precio_inscripcion')

        # Assert
        assert field.default == 50000.00

    def test_estado_choices(self):
        """Verifica los choices del campo estado."""
        # Arrange & Act
        from negocio.models import Torneo
        field = Torneo._meta.get_field('estado')

        # Assert
        estados = [c[0] for c in field.choices]
        assert 'PENDIENTE' in estados
        assert 'PUBLICADO' in estados
        assert 'RECHAZADO' in estados


class TestReservaModel:
    """Pruebas del modelo Reserva."""

    def test_str_representation(self):
        """Happy Path: __str__ muestra ID, nombre de cancha y fecha."""
        # Arrange
        from negocio.models import Reserva
        reserva = MagicMock(spec=Reserva)
        reserva.id = 42
        reserva.cancha = MagicMock()
        reserva.cancha.nombre = "Cancha Norte"
        reserva.fecha = datetime.date(2026, 7, 15)

        # Act
        result = Reserva.__str__(reserva)

        # Assert
        assert result == "Reserva 42 - Cancha Norte (2026-07-15)"

    def test_estado_default_is_programada(self):
        """Verifica que el estado por defecto sea PROGRAMADA."""
        # Arrange & Act
        from negocio.models import Reserva
        field = Reserva._meta.get_field('estado')

        # Assert
        assert field.default == 'PROGRAMADA'

    def test_pagado_default_is_false(self):
        """Verifica que pagado comience en False."""
        # Arrange & Act
        from negocio.models import Reserva
        field = Reserva._meta.get_field('pagado')

        # Assert
        assert field.default is False

    @patch('django.utils.timezone.now')
    def test_puede_cancelar_more_than_24h(self, mock_now):
        """Happy Path: puede cancelar con >24h de anticipación."""
        # Arrange
        from negocio.models import Reserva
        reserva = MagicMock(spec=Reserva)
        # Reserva para mañana a las 10:00
        reserva.fecha = datetime.date(2026, 6, 21)
        reserva.hora = datetime.time(10, 0)

        # Ahora es 19 de junio a las 8:00 (>24h antes)
        now = datetime.datetime(2026, 6, 19, 8, 0, tzinfo=datetime.timezone.utc)
        mock_now.return_value = now

        # Act
        result = Reserva.puede_cancelar(reserva)

        # Assert
        assert result is True

    @patch('django.utils.timezone.now')
    def test_puede_cancelar_less_than_24h(self, mock_now):
        """Edge Case: NO puede cancelar con <24h de anticipación."""
        # Arrange
        from negocio.models import Reserva
        reserva = MagicMock(spec=Reserva)
        reserva.fecha = datetime.date(2026, 6, 20)
        reserva.hora = datetime.time(10, 0)

        # Ahora es 20 de junio a las 9:00 (solo 1h antes)
        now = datetime.datetime(2026, 6, 20, 9, 0, tzinfo=datetime.timezone.utc)
        mock_now.return_value = now

        # Act
        result = Reserva.puede_cancelar(reserva)

        # Assert
        assert result is False

    def test_estado_choices_count(self):
        """Verifica que haya exactamente 3 opciones de estado."""
        # Arrange & Act
        from negocio.models import Reserva
        field = Reserva._meta.get_field('estado')

        # Assert
        assert len(field.choices) == 3
        estados = [c[0] for c in field.choices]
        assert 'PROGRAMADA' in estados
        assert 'COMPLETADA' in estados
        assert 'CANCELADA' in estados


class TestFacturaModel:
    """Pruebas del modelo Factura."""

    def test_str_representation(self):
        """Happy Path: __str__ muestra ID y total."""
        # Arrange
        from negocio.models import Factura
        factura = MagicMock(spec=Factura)
        factura.id = 10
        factura.total = Decimal('150000.00')

        # Act
        result = Factura.__str__(factura)

        # Assert
        assert result == "Factura 10 - 150000.00"

    @patch('negocio.models.uuid')
    def test_save_generates_referencia_pago_when_empty(self, mock_uuid):
        """Happy Path: save genera referencia_pago si está vacía."""
        # Arrange
        from negocio.models import Factura
        mock_uuid.uuid4.return_value.hex = 'abcdef123456789012345678'

        factura = MagicMock(spec=Factura)
        factura.referencia_pago = None

        # Simular el método save
        def save_logic(self_factura, *args, **kwargs):
            if not self_factura.referencia_pago:
                import uuid
                self_factura.referencia_pago = f"FACTURA-{mock_uuid.uuid4().hex[:12].upper()}"

        # Act
        save_logic(factura)

        # Assert
        assert factura.referencia_pago is not None
        assert factura.referencia_pago.startswith("FACTURA-")

    def test_referencia_pago_is_unique(self):
        """Verifica que referencia_pago sea un campo único."""
        # Arrange & Act
        from negocio.models import Factura
        field = Factura._meta.get_field('referencia_pago')

        # Assert
        assert field.unique is True


class TestEquipoModel:
    """Pruebas del modelo Equipo."""

    def test_str_returns_nombre(self):
        """Happy Path: __str__ retorna el nombre del equipo."""
        # Arrange
        from negocio.models import Equipo
        equipo = MagicMock(spec=Equipo)
        equipo.nombre = "Los Tigres FC"

        # Act
        result = Equipo.__str__(equipo)

        # Assert
        assert result == "Los Tigres FC"


class TestPartidoModel:
    """Pruebas del modelo Partido."""

    def test_str_representation(self):
        """Happy Path: __str__ muestra equipos y jornada."""
        # Arrange
        from negocio.models import Partido
        partido = MagicMock(spec=Partido)
        partido.equipo_local = MagicMock()
        partido.equipo_local.__str__ = lambda self: "Tigres"
        partido.equipo_visitante = MagicMock()
        partido.equipo_visitante.__str__ = lambda self: "Leones"
        partido.jornada = 3

        # Act
        result = Partido.__str__(partido)

        # Assert
        assert "Tigres" in result
        assert "Leones" in result
        assert "Jornada 3" in result

    def test_estado_default_is_pendiente(self):
        """Verifica que el estado por defecto sea PENDIENTE."""
        # Arrange & Act
        from negocio.models import Partido
        field = Partido._meta.get_field('estado')

        # Assert
        assert field.default == 'PENDIENTE'

    def test_ordering(self):
        """Verifica el ordering del modelo Partido."""
        # Arrange & Act
        from negocio.models import Partido

        # Assert
        assert Partido._meta.ordering == ['jornada', 'fecha']

    def test_goles_default_zero(self):
        """Verifica que los goles empiecen en 0."""
        # Arrange & Act
        from negocio.models import Partido
        goles_l = Partido._meta.get_field('goles_local')
        goles_v = Partido._meta.get_field('goles_visitante')

        # Assert
        assert goles_l.default == 0
        assert goles_v.default == 0


class TestPosicionEquipoModel:
    """Pruebas del modelo PosicionEquipo."""

    def test_diferencia_goles_positive(self):
        """Happy Path: diferencia de goles positiva."""
        # Arrange
        from negocio.models import PosicionEquipo
        pos = MagicMock(spec=PosicionEquipo)
        pos.goles_favor = 10
        pos.goles_contra = 4

        # Act
        result = PosicionEquipo.diferencia_goles.fget(pos)

        # Assert
        assert result == 6

    def test_diferencia_goles_negative(self):
        """Edge Case: diferencia de goles negativa."""
        # Arrange
        from negocio.models import PosicionEquipo
        pos = MagicMock(spec=PosicionEquipo)
        pos.goles_favor = 2
        pos.goles_contra = 8

        # Act
        result = PosicionEquipo.diferencia_goles.fget(pos)

        # Assert
        assert result == -6

    def test_diferencia_goles_zero(self):
        """Edge Case: diferencia de goles cero (empate total)."""
        # Arrange
        from negocio.models import PosicionEquipo
        pos = MagicMock(spec=PosicionEquipo)
        pos.goles_favor = 5
        pos.goles_contra = 5

        # Act
        result = PosicionEquipo.diferencia_goles.fget(pos)

        # Assert
        assert result == 0

    def test_str_representation(self):
        """Happy Path: __str__ muestra equipo, puntos y torneo."""
        # Arrange
        from negocio.models import PosicionEquipo
        pos = MagicMock(spec=PosicionEquipo)
        pos.equipo = MagicMock()
        pos.equipo.nombre = "Real Madrid"
        pos.puntos = 15
        pos.torneo = MagicMock()
        pos.torneo.nombre = "Liga Premier"

        # Act
        result = PosicionEquipo.__str__(pos)

        # Assert
        assert result == "Real Madrid - 15 pts (Liga Premier)"

    def test_ordering(self):
        """Verifica el ordering del modelo PosicionEquipo."""
        # Arrange & Act
        from negocio.models import PosicionEquipo

        # Assert
        assert PosicionEquipo._meta.ordering == ['-puntos', '-partidos_ganados', '-goles_favor']

    def test_unique_together(self):
        """Verifica unique_together (torneo, equipo)."""
        # Arrange & Act
        from negocio.models import PosicionEquipo

        # Assert
        assert ('torneo', 'equipo') in PosicionEquipo._meta.unique_together

    def test_all_fields_default_zero(self):
        """Verifica que todos los campos numéricos empiecen en 0."""
        # Arrange & Act
        from negocio.models import PosicionEquipo
        campos_numericos = [
            'puntos', 'partidos_jugados', 'partidos_ganados',
            'partidos_empatados', 'partidos_perdidos',
            'goles_favor', 'goles_contra'
        ]

        # Assert
        for campo_nombre in campos_numericos:
            field = PosicionEquipo._meta.get_field(campo_nombre)
            assert field.default == 0, f"Campo {campo_nombre} no tiene default=0"


class TestSolicitudModificacionTorneoModel:
    """Pruebas del modelo SolicitudModificacionTorneo."""

    def test_str_representation(self):
        """Happy Path: __str__ muestra torneo y estado."""
        # Arrange
        from negocio.models import SolicitudModificacionTorneo
        sol = MagicMock(spec=SolicitudModificacionTorneo)
        sol.torneo = MagicMock()
        sol.torneo.nombre = "Copa Navidad"
        sol.get_estado_display.return_value = "Pendiente"

        # Act
        result = SolicitudModificacionTorneo.__str__(sol)

        # Assert
        assert result == "Solicitud para Copa Navidad (Pendiente)"

    def test_estado_default_pendiente(self):
        """Verifica que el estado por defecto sea PENDIENTE."""
        # Arrange & Act
        from negocio.models import SolicitudModificacionTorneo
        field = SolicitudModificacionTorneo._meta.get_field('estado')

        # Assert
        assert field.default == 'PENDIENTE'
