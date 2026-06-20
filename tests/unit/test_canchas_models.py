"""
Pruebas unitarias para canchas/models.py

Componentes probados:
- Deporte: representación en string.
- Cancha: representación en string, promedio_calificacion, total_calificaciones.
- Disponibilidad: representación en string, Meta.unique_together.
- Calificacion: representación en string, Meta.ordering.
"""
import pytest
from unittest.mock import MagicMock, PropertyMock, patch


class TestDeporteModel:
    """Pruebas del modelo Deporte."""

    def test_str_returns_nombre(self):
        """Happy Path: __str__ retorna el nombre del deporte."""
        # Arrange
        from canchas.models import Deporte
        deporte = MagicMock(spec=Deporte)
        deporte.nombre = "Fútbol"

        # Act
        result = Deporte.__str__(deporte)

        # Assert
        assert result == "Fútbol"

    def test_nombre_is_unique(self):
        """Verifica que el nombre sea único a nivel de modelo."""
        # Arrange & Act
        from canchas.models import Deporte
        field = Deporte._meta.get_field('nombre')

        # Assert
        assert field.unique is True


class TestCanchaModel:
    """Pruebas del modelo Cancha."""

    def test_str_returns_nombre(self):
        """Happy Path: __str__ retorna el nombre de la cancha."""
        # Arrange
        from canchas.models import Cancha
        cancha = MagicMock(spec=Cancha)
        cancha.nombre = "Cancha Principal"

        # Act
        result = Cancha.__str__(cancha)

        # Assert
        assert result == "Cancha Principal"

    def test_promedio_calificacion_with_reviews(self):
        """Happy Path: promedio con calificaciones existentes."""
        # Arrange
        from canchas.models import Cancha

        mock_cal1 = MagicMock()
        mock_cal1.puntuacion = 4
        mock_cal2 = MagicMock()
        mock_cal2.puntuacion = 5
        mock_cal3 = MagicMock()
        mock_cal3.puntuacion = 3

        cancha = MagicMock(spec=Cancha)
        mock_qs = MagicMock()
        mock_qs.exists.return_value = True
        mock_qs.count.return_value = 3
        mock_qs.__iter__ = lambda self: iter([mock_cal1, mock_cal2, mock_cal3])
        cancha.calificaciones.all.return_value = mock_qs

        # Act
        result = Cancha.promedio_calificacion.fget(cancha)

        # Assert
        assert result == 4.0  # (4+5+3)/3 = 4.0

    def test_promedio_calificacion_without_reviews(self):
        """Edge Case: sin calificaciones debe retornar None."""
        # Arrange
        from canchas.models import Cancha

        cancha = MagicMock(spec=Cancha)
        mock_qs = MagicMock()
        mock_qs.exists.return_value = False
        cancha.calificaciones.all.return_value = mock_qs

        # Act
        result = Cancha.promedio_calificacion.fget(cancha)

        # Assert
        assert result is None

    def test_total_calificaciones(self):
        """Happy Path: total de calificaciones."""
        # Arrange
        from canchas.models import Cancha
        cancha = MagicMock(spec=Cancha)
        cancha.calificaciones.count.return_value = 7

        # Act
        result = Cancha.total_calificaciones.fget(cancha)

        # Assert
        assert result == 7

    def test_total_calificaciones_zero(self):
        """Edge Case: cero calificaciones."""
        # Arrange
        from canchas.models import Cancha
        cancha = MagicMock(spec=Cancha)
        cancha.calificaciones.count.return_value = 0

        # Act
        result = Cancha.total_calificaciones.fget(cancha)

        # Assert
        assert result == 0

    def test_promedio_calificacion_rounding(self):
        """Edge Case: el promedio se redondea a 1 decimal."""
        # Arrange
        from canchas.models import Cancha

        mock_cal1 = MagicMock()
        mock_cal1.puntuacion = 3
        mock_cal2 = MagicMock()
        mock_cal2.puntuacion = 4

        cancha = MagicMock(spec=Cancha)
        mock_qs = MagicMock()
        mock_qs.exists.return_value = True
        mock_qs.count.return_value = 2
        mock_qs.__iter__ = lambda self: iter([mock_cal1, mock_cal2])
        cancha.calificaciones.all.return_value = mock_qs

        # Act
        result = Cancha.promedio_calificacion.fget(cancha)

        # Assert
        assert result == 3.5  # (3+4)/2 = 3.5

    def test_ciudad_default_bogota(self):
        """Verifica que el default de ciudad sea Bogotá."""
        # Arrange & Act
        from canchas.models import Cancha
        field = Cancha._meta.get_field('ciudad')

        # Assert
        assert field.default == 'Bogotá'


class TestDisponibilidadModel:
    """Pruebas del modelo Disponibilidad."""

    def test_str_representation(self):
        """Happy Path: representación en string."""
        # Arrange
        from canchas.models import Disponibilidad
        import datetime

        disp = MagicMock(spec=Disponibilidad)
        disp.cancha = MagicMock()
        disp.cancha.nombre = "Cancha Norte"
        disp.get_dia_semana_display.return_value = "Lunes"
        disp.hora_inicio = datetime.time(8, 0)
        disp.hora_fin = datetime.time(18, 0)

        # Act
        result = Disponibilidad.__str__(disp)

        # Assert
        assert "Cancha Norte" in result
        assert "Lunes" in result

    def test_unique_together_constraint(self):
        """Verifica unique_together del modelo."""
        # Arrange & Act
        from canchas.models import Disponibilidad
        unique = Disponibilidad._meta.unique_together

        # Assert
        assert ('cancha', 'dia_semana', 'hora_inicio', 'hora_fin') in unique

    def test_dia_choices_has_seven_days(self):
        """Verifica que DIA_CHOICES tenga 7 opciones (Lunes a Domingo)."""
        # Arrange & Act
        from canchas.models import Disponibilidad

        # Assert
        assert len(Disponibilidad.DIA_CHOICES) == 7
        assert Disponibilidad.DIA_CHOICES[0] == (0, 'Lunes')
        assert Disponibilidad.DIA_CHOICES[6] == (6, 'Domingo')


class TestCalificacionModel:
    """Pruebas del modelo Calificacion."""

    def test_str_representation(self):
        """Happy Path: representación en string de una calificación."""
        # Arrange
        from canchas.models import Calificacion

        cal = MagicMock(spec=Calificacion)
        cal.usuario = MagicMock()
        cal.usuario.username = "juana"
        cal.cancha = MagicMock()
        cal.cancha.nombre = "Cancha Sur"
        cal.puntuacion = 5

        # Act
        result = Calificacion.__str__(cal)

        # Assert
        assert result == "juana - Cancha Sur (5★)"

    def test_unique_together_usuario_cancha(self):
        """Verifica unique_together (cancha, usuario)."""
        # Arrange & Act
        from canchas.models import Calificacion
        unique = Calificacion._meta.unique_together

        # Assert
        assert ('cancha', 'usuario') in unique

    def test_ordering_by_fecha_desc(self):
        """Verifica que el ordering sea por fecha descendente."""
        # Arrange & Act
        from canchas.models import Calificacion

        # Assert
        assert Calificacion._meta.ordering == ['-fecha_creacion']

    def test_puntuacion_validators(self):
        """Verifica que puntuación tenga validadores de rango 1-5."""
        # Arrange & Act
        from canchas.models import Calificacion
        field = Calificacion._meta.get_field('puntuacion')

        # Assert
        validator_classes = [v.__class__.__name__ for v in field.validators]
        assert 'MinValueValidator' in validator_classes
        assert 'MaxValueValidator' in validator_classes
