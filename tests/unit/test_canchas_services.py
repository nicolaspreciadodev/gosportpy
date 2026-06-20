"""
Pruebas unitarias para canchas/services.py

Componentes probados:
- obtener_canchas_del_dueño: filtrado de canchas por dueño.
- crear_cancha: asignación de dueño y persistencia.
- verificar_propiedad: validación de propiedad con PermissionDenied.
- _generar_slots_por_hora: generación de slots horarios.
- obtener_slots_disponibles: disponibilidad de slots en una fecha.
- validar_slot_disponible: validación de un slot específico.
- puede_calificar_cancha: verificación de reserva completada.
- crear_calificacion: creación con validaciones completas.
- obtener_calificaciones_cancha: listado de calificaciones.
"""
import pytest
import datetime
from unittest.mock import MagicMock, patch, PropertyMock
from django.core.exceptions import PermissionDenied, ValidationError


class TestObtenerCanchasDelDueno:
    """Pruebas para obtener_canchas_del_dueño."""

    @patch('canchas.services.Cancha.objects')
    def test_happy_path_returns_filtered_queryset(self, mock_objects):
        """Happy Path: retorna canchas filtradas por dueño."""
        # Arrange
        mock_usuario = MagicMock()
        mock_qs = MagicMock()
        mock_objects.filter.return_value.select_related.return_value = mock_qs

        # Act
        from canchas.services import obtener_canchas_del_dueño
        result = obtener_canchas_del_dueño(mock_usuario)

        # Assert
        mock_objects.filter.assert_called_once_with(dueño=mock_usuario)
        assert result == mock_qs

    @patch('canchas.services.Cancha.objects')
    def test_no_canchas_returns_empty(self, mock_objects):
        """Edge Case: dueño sin canchas retorna QuerySet vacío."""
        # Arrange
        mock_usuario = MagicMock()
        mock_qs = MagicMock()
        mock_qs.count.return_value = 0
        mock_objects.filter.return_value.select_related.return_value = mock_qs

        # Act
        from canchas.services import obtener_canchas_del_dueño
        result = obtener_canchas_del_dueño(mock_usuario)

        # Assert
        assert result.count() == 0


class TestCrearCancha:
    """Pruebas para crear_cancha."""

    def test_happy_path_assigns_owner_and_saves(self):
        """Happy Path: asigna dueño y guarda correctamente."""
        # Arrange
        mock_form = MagicMock()
        mock_dueno = MagicMock()

        # Act
        from canchas.services import crear_cancha
        result = crear_cancha(mock_form, mock_dueno)

        # Assert
        assert mock_form.dueño == mock_dueno
        mock_form.save.assert_called_once()
        assert result == mock_form

    def test_returns_form_instance(self):
        """Verifica que retorna la instancia del formulario."""
        # Arrange
        mock_form = MagicMock()
        mock_dueno = MagicMock()

        # Act
        from canchas.services import crear_cancha
        result = crear_cancha(mock_form, mock_dueno)

        # Assert
        assert result is mock_form


class TestVerificarPropiedad:
    """Pruebas para verificar_propiedad."""

    def test_happy_path_owner_passes(self):
        """Happy Path: dueño correcto no lanza excepción."""
        # Arrange
        mock_usuario = MagicMock()
        mock_cancha = MagicMock()
        mock_cancha.dueño = mock_usuario

        # Act & Assert (no debe lanzar excepción)
        from canchas.services import verificar_propiedad
        verificar_propiedad(mock_cancha, mock_usuario)

    def test_non_owner_raises_permission_denied(self):
        """Edge Case: usuario no dueño lanza PermissionDenied."""
        # Arrange
        mock_usuario = MagicMock()
        mock_otro = MagicMock()
        mock_cancha = MagicMock()
        mock_cancha.dueño = mock_otro

        # Act & Assert
        from canchas.services import verificar_propiedad
        with pytest.raises(PermissionDenied, match="No tienes permiso"):
            verificar_propiedad(mock_cancha, mock_usuario)


class TestGenerarSlotsPorHora:
    """Pruebas para _generar_slots_por_hora."""

    def test_happy_path_three_hour_range(self):
        """Happy Path: rango de 3 horas genera 3 slots."""
        # Arrange
        hora_inicio = datetime.time(8, 0)
        hora_fin = datetime.time(11, 0)

        # Act
        from canchas.services import _generar_slots_por_hora
        result = _generar_slots_por_hora(hora_inicio, hora_fin)

        # Assert
        assert len(result) == 3
        assert result[0] == datetime.time(8, 0)
        assert result[1] == datetime.time(9, 0)
        assert result[2] == datetime.time(10, 0)

    def test_single_hour_range(self):
        """Edge Case: rango de 1 hora genera 1 slot."""
        # Arrange
        hora_inicio = datetime.time(14, 0)
        hora_fin = datetime.time(15, 0)

        # Act
        from canchas.services import _generar_slots_por_hora
        result = _generar_slots_por_hora(hora_inicio, hora_fin)

        # Assert
        assert len(result) == 1
        assert result[0] == datetime.time(14, 0)

    def test_same_start_end_returns_empty(self):
        """Edge Case: hora_inicio == hora_fin retorna lista vacía."""
        # Arrange
        hora_inicio = datetime.time(10, 0)
        hora_fin = datetime.time(10, 0)

        # Act
        from canchas.services import _generar_slots_por_hora
        result = _generar_slots_por_hora(hora_inicio, hora_fin)

        # Assert
        assert result == []

    def test_full_day_range(self):
        """Edge Case: rango completo de día laboral (8 a 20 = 12 slots)."""
        # Arrange
        hora_inicio = datetime.time(8, 0)
        hora_fin = datetime.time(20, 0)

        # Act
        from canchas.services import _generar_slots_por_hora
        result = _generar_slots_por_hora(hora_inicio, hora_fin)

        # Assert
        assert len(result) == 12


class TestObtenerSlotsDisponibles:
    """Pruebas para obtener_slots_disponibles."""

    @patch('canchas.services.apps.get_model')
    @patch('canchas.services.Cancha.objects')
    def test_happy_path_with_no_reservations(self, mock_cancha_objects, mock_get_model):
        """Happy Path: todos los slots disponibles sin reservas."""
        # Arrange
        fecha = datetime.date(2026, 6, 23)  # Lunes
        mock_cancha = MagicMock()
        mock_disp = MagicMock()
        mock_disp.hora_inicio = datetime.time(8, 0)
        mock_disp.hora_fin = datetime.time(11, 0)
        mock_cancha.disponibilidades.filter.return_value = [mock_disp]
        mock_cancha_objects.get.return_value = mock_cancha

        mock_reserva_model = MagicMock()
        mock_reserva_model.objects.filter.return_value.exclude.return_value.values_list.return_value = []
        mock_get_model.return_value = mock_reserva_model

        # Act
        from canchas.services import obtener_slots_disponibles
        result = obtener_slots_disponibles(1, fecha)

        # Assert
        assert len(result) == 3
        assert datetime.time(8, 0) in result
        assert datetime.time(9, 0) in result
        assert datetime.time(10, 0) in result

    @patch('canchas.services.apps.get_model')
    @patch('canchas.services.Cancha.objects')
    def test_slots_exclude_reserved_hours(self, mock_cancha_objects, mock_get_model):
        """Happy Path: excluye slots con reservas existentes."""
        # Arrange
        fecha = datetime.date(2026, 6, 23)
        mock_cancha = MagicMock()
        mock_disp = MagicMock()
        mock_disp.hora_inicio = datetime.time(8, 0)
        mock_disp.hora_fin = datetime.time(11, 0)
        mock_cancha.disponibilidades.filter.return_value = [mock_disp]
        mock_cancha_objects.get.return_value = mock_cancha

        mock_reserva_model = MagicMock()
        mock_reserva_model.objects.filter.return_value.exclude.return_value.values_list.return_value = [
            datetime.time(9, 0)
        ]
        mock_get_model.return_value = mock_reserva_model

        # Act
        from canchas.services import obtener_slots_disponibles
        result = obtener_slots_disponibles(1, fecha)

        # Assert
        assert len(result) == 2
        assert datetime.time(9, 0) not in result

    @patch('canchas.services.apps.get_model')
    @patch('canchas.services.Cancha.objects')
    def test_all_slots_reserved_returns_empty(self, mock_cancha_objects, mock_get_model):
        """Edge Case: todos los slots reservados retorna lista vacía."""
        # Arrange
        fecha = datetime.date(2026, 6, 23)
        mock_cancha = MagicMock()
        mock_disp = MagicMock()
        mock_disp.hora_inicio = datetime.time(8, 0)
        mock_disp.hora_fin = datetime.time(10, 0)
        mock_cancha.disponibilidades.filter.return_value = [mock_disp]
        mock_cancha_objects.get.return_value = mock_cancha

        mock_reserva_model = MagicMock()
        mock_reserva_model.objects.filter.return_value.exclude.return_value.values_list.return_value = [
            datetime.time(8, 0), datetime.time(9, 0)
        ]
        mock_get_model.return_value = mock_reserva_model

        # Act
        from canchas.services import obtener_slots_disponibles
        result = obtener_slots_disponibles(1, fecha)

        # Assert
        assert result == []

    @patch('canchas.services.apps.get_model')
    @patch('canchas.services.Cancha.objects')
    def test_fecha_string_is_parsed(self, mock_cancha_objects, mock_get_model):
        """Edge Case: fecha como string se convierte correctamente."""
        # Arrange
        fecha_str = '2026-06-23'
        mock_cancha = MagicMock()
        mock_cancha.disponibilidades.filter.return_value = []
        mock_cancha_objects.get.return_value = mock_cancha

        mock_reserva_model = MagicMock()
        mock_reserva_model.objects.filter.return_value.exclude.return_value.values_list.return_value = []
        mock_get_model.return_value = mock_reserva_model

        # Act
        from canchas.services import obtener_slots_disponibles
        result = obtener_slots_disponibles(1, fecha_str)

        # Assert
        assert isinstance(result, list)


class TestValidarSlotDisponible:
    """Pruebas para validar_slot_disponible."""

    @patch('canchas.services.obtener_slots_disponibles')
    def test_happy_path_slot_available(self, mock_obtener):
        """Happy Path: slot disponible retorna True."""
        # Arrange
        mock_obtener.return_value = [datetime.time(8, 0), datetime.time(9, 0)]

        # Act
        from canchas.services import validar_slot_disponible
        result = validar_slot_disponible(1, '2026-06-23', datetime.time(8, 0))

        # Assert
        assert result is True

    @patch('canchas.services.obtener_slots_disponibles')
    def test_slot_not_available(self, mock_obtener):
        """Edge Case: slot no disponible retorna False."""
        # Arrange
        mock_obtener.return_value = [datetime.time(8, 0)]

        # Act
        from canchas.services import validar_slot_disponible
        result = validar_slot_disponible(1, '2026-06-23', datetime.time(10, 0))

        # Assert
        assert result is False

    @patch('canchas.services.obtener_slots_disponibles')
    def test_hora_string_hh_mm_ss_format(self, mock_obtener):
        """Edge Case: hora en formato HH:MM:SS se parsea correctamente."""
        # Arrange
        mock_obtener.return_value = [datetime.time(14, 0)]

        # Act
        from canchas.services import validar_slot_disponible
        result = validar_slot_disponible(1, '2026-06-23', '14:00:00')

        # Assert
        assert result is True

    @patch('canchas.services.obtener_slots_disponibles')
    def test_hora_string_hh_mm_format(self, mock_obtener):
        """Edge Case: hora en formato HH:MM se parsea correctamente."""
        # Arrange
        mock_obtener.return_value = [datetime.time(14, 0)]

        # Act
        from canchas.services import validar_slot_disponible
        result = validar_slot_disponible(1, '2026-06-23', '14:00')

        # Assert
        assert result is True


class TestPuedeCalificarCancha:
    """Pruebas para puede_calificar_cancha."""

    @patch('canchas.services.apps.get_model')
    def test_happy_path_user_can_rate(self, mock_get_model):
        """Happy Path: usuario con reserva completada puede calificar."""
        # Arrange
        mock_reserva_model = MagicMock()
        mock_reserva_model.objects.filter.return_value.exists.return_value = True
        mock_get_model.return_value = mock_reserva_model
        mock_usuario = MagicMock()
        mock_cancha = MagicMock()

        # Act
        from canchas.services import puede_calificar_cancha
        result = puede_calificar_cancha(mock_usuario, mock_cancha)

        # Assert
        assert result is True

    @patch('canchas.services.apps.get_model')
    def test_user_without_completed_reservation_cannot_rate(self, mock_get_model):
        """Edge Case: usuario sin reserva completada no puede calificar."""
        # Arrange
        mock_reserva_model = MagicMock()
        mock_reserva_model.objects.filter.return_value.exists.return_value = False
        mock_get_model.return_value = mock_reserva_model
        mock_usuario = MagicMock()
        mock_cancha = MagicMock()

        # Act
        from canchas.services import puede_calificar_cancha
        result = puede_calificar_cancha(mock_usuario, mock_cancha)

        # Assert
        assert result is False


class TestCrearCalificacion:
    """Pruebas para crear_calificacion."""

    @patch('canchas.models.Calificacion.objects')
    @patch('canchas.services.puede_calificar_cancha')
    def test_happy_path_creates_rating(self, mock_puede, mock_cal_objects):
        """Happy Path: crea calificación exitosamente."""
        # Arrange
        mock_puede.return_value = True
        mock_cal_objects.filter.return_value.exists.return_value = False
        mock_calificacion_instance = MagicMock()
        mock_cal_objects.create.return_value = mock_calificacion_instance
        mock_usuario = MagicMock()
        mock_cancha = MagicMock()

        # Act
        from canchas.services import crear_calificacion
        result = crear_calificacion(mock_usuario, mock_cancha, 5, "Excelente cancha")

        # Assert
        mock_cal_objects.create.assert_called_once_with(
            usuario=mock_usuario,
            cancha=mock_cancha,
            puntuacion=5,
            comentario="Excelente cancha"
        )
        assert result == mock_calificacion_instance

    @patch('canchas.services.puede_calificar_cancha')
    def test_no_completed_reservation_raises_permission_denied(self, mock_puede):
        """Edge Case: sin reserva completada lanza PermissionDenied."""
        # Arrange
        mock_puede.return_value = False
        mock_usuario = MagicMock()
        mock_cancha = MagicMock()

        # Act & Assert
        from canchas.services import crear_calificacion
        with pytest.raises(PermissionDenied, match="Solo puedes calificar"):
            crear_calificacion(mock_usuario, mock_cancha, 5)

    @patch('canchas.models.Calificacion.objects')
    @patch('canchas.services.puede_calificar_cancha')
    def test_duplicate_rating_raises_validation_error(self, mock_puede, mock_cal_objects):
        """Edge Case: calificación duplicada lanza ValidationError."""
        # Arrange
        mock_puede.return_value = True
        mock_cal_objects.filter.return_value.exists.return_value = True
        mock_usuario = MagicMock()
        mock_cancha = MagicMock()

        # Act & Assert
        from canchas.services import crear_calificacion
        with pytest.raises(ValidationError, match="Ya habías calificado"):
            crear_calificacion(mock_usuario, mock_cancha, 4)

    @patch('canchas.models.Calificacion.objects')
    @patch('canchas.services.puede_calificar_cancha')
    def test_invalid_score_zero_raises(self, mock_puede, mock_cal_objects):
        """Edge Case: puntuación 0 lanza ValidationError."""
        # Arrange
        mock_puede.return_value = True
        mock_cal_objects.filter.return_value.exists.return_value = False
        mock_usuario = MagicMock()
        mock_cancha = MagicMock()

        # Act & Assert
        from canchas.services import crear_calificacion
        with pytest.raises(ValidationError, match="entre 1 y 5"):
            crear_calificacion(mock_usuario, mock_cancha, 0)

    @patch('canchas.models.Calificacion.objects')
    @patch('canchas.services.puede_calificar_cancha')
    def test_invalid_score_six_raises(self, mock_puede, mock_cal_objects):
        """Edge Case: puntuación 6 lanza ValidationError."""
        # Arrange
        mock_puede.return_value = True
        mock_cal_objects.filter.return_value.exists.return_value = False
        mock_usuario = MagicMock()
        mock_cancha = MagicMock()

        # Act & Assert
        from canchas.services import crear_calificacion
        with pytest.raises(ValidationError, match="entre 1 y 5"):
            crear_calificacion(mock_usuario, mock_cancha, 6)

    @patch('canchas.models.Calificacion.objects')
    @patch('canchas.services.puede_calificar_cancha')
    def test_comment_is_stripped(self, mock_puede, mock_cal_objects):
        """Edge Case: el comentario se limpia de espacios laterales."""
        # Arrange
        mock_puede.return_value = True
        mock_cal_objects.filter.return_value.exists.return_value = False
        mock_cal_objects.create.return_value = MagicMock()
        mock_usuario = MagicMock()
        mock_cancha = MagicMock()

        # Act
        from canchas.services import crear_calificacion
        crear_calificacion(mock_usuario, mock_cancha, 4, "  Buena cancha  ")

        # Assert
        mock_cal_objects.create.assert_called_once_with(
            usuario=mock_usuario,
            cancha=mock_cancha,
            puntuacion=4,
            comentario="Buena cancha"
        )


class TestObtenerCalificacionesCancha:
    """Pruebas para obtener_calificaciones_cancha."""

    @patch('canchas.models.Calificacion.objects')
    def test_happy_path_returns_queryset(self, mock_cal_objects):
        """Happy Path: retorna queryset de calificaciones."""
        # Arrange
        mock_qs = MagicMock()
        mock_cal_objects.filter.return_value.select_related.return_value = mock_qs
        mock_cancha = MagicMock()

        # Act
        from canchas.services import obtener_calificaciones_cancha
        result = obtener_calificaciones_cancha(mock_cancha)

        # Assert
        mock_cal_objects.filter.assert_called_once_with(cancha=mock_cancha)
        assert result == mock_qs
