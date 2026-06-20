"""
Pruebas unitarias para negocio/services.py

Componentes probados:
- inscribir_equipo_torneo: inscripción con validaciones de límite y duplicado.
- generar_fixture_liga: generación de fixture Round-Robin con validaciones.
- registrar_resultado: registro de resultado con validaciones de permisos.
- _actualizar_posiciones: recálculo idempotente de la tabla de posiciones.
"""
import pytest
from unittest.mock import MagicMock, patch
from django.core.exceptions import ValidationError


class TestInscribirEquipoTorneo:
    """Pruebas para inscribir_equipo_torneo."""

    def test_happy_path_inscribe_equipo(self):
        """Happy Path: inscribe equipo exitosamente."""
        # Arrange
        mock_equipo = MagicMock()
        mock_equipo.id = 1
        mock_torneo = MagicMock()
        mock_torneo.max_equipos = 8
        mock_torneo.equipos.count.return_value = 3
        mock_torneo.equipos.filter.return_value.exists.return_value = False

        # Act
        from negocio.services import inscribir_equipo_torneo
        inscribir_equipo_torneo(mock_equipo, mock_torneo)

        # Assert
        mock_torneo.equipos.add.assert_called_once_with(mock_equipo)

    def test_torneo_full_raises_validation_error(self):
        """Edge Case: torneo lleno lanza ValidationError."""
        # Arrange
        mock_equipo = MagicMock()
        mock_torneo = MagicMock()
        mock_torneo.max_equipos = 4
        mock_torneo.equipos.count.return_value = 4

        # Act & Assert
        from negocio.services import inscribir_equipo_torneo
        with pytest.raises(ValidationError, match="límite"):
            inscribir_equipo_torneo(mock_equipo, mock_torneo)

    def test_equipo_already_inscribed_raises_validation_error(self):
        """Edge Case: equipo ya inscrito lanza ValidationError."""
        # Arrange
        mock_equipo = MagicMock()
        mock_equipo.id = 1
        mock_torneo = MagicMock()
        mock_torneo.max_equipos = 8
        mock_torneo.equipos.count.return_value = 3
        mock_torneo.equipos.filter.return_value.exists.return_value = True

        # Act & Assert
        from negocio.services import inscribir_equipo_torneo
        with pytest.raises(ValidationError, match="ya está inscrito"):
            inscribir_equipo_torneo(mock_equipo, mock_torneo)

    def test_inscribe_when_one_slot_left(self):
        """Edge Case: inscribe equipo cuando queda exactamente 1 cupo."""
        # Arrange
        mock_equipo = MagicMock()
        mock_equipo.id = 5
        mock_torneo = MagicMock()
        mock_torneo.max_equipos = 8
        mock_torneo.equipos.count.return_value = 7
        mock_torneo.equipos.filter.return_value.exists.return_value = False

        # Act
        from negocio.services import inscribir_equipo_torneo
        inscribir_equipo_torneo(mock_equipo, mock_torneo)

        # Assert
        mock_torneo.equipos.add.assert_called_once_with(mock_equipo)


class TestGenerarFixtureLiga:
    """Pruebas para generar_fixture_liga."""

    @patch('negocio.services.Partido')
    @patch('negocio.services.PosicionEquipo')
    def test_happy_path_four_teams(self, mock_PosicionEquipo, mock_Partido):
        """Happy Path: genera fixture con 4 equipos (6 partidos, 3 jornadas)."""
        # Arrange
        mock_PosicionEquipo.objects.get_or_create.return_value = (MagicMock(), True)

        equipos = [MagicMock() for _ in range(4)]
        mock_torneo = MagicMock()
        mock_torneo.formato = 'LIGA'
        mock_torneo.fixture_generado = False
        mock_torneo.equipos.all.return_value = equipos

        # Act
        from negocio.services import generar_fixture_liga
        result = generar_fixture_liga(mock_torneo)

        # Assert
        assert result is True
        assert mock_torneo.fixture_generado is True
        mock_torneo.save.assert_called_once()
        # 4 equipos: 3 jornadas x 2 partidos = 6 partidos
        assert mock_Partido.objects.create.call_count == 6

    def test_formato_not_liga_raises(self):
        """Edge Case: formato != LIGA lanza ValidationError."""
        # Arrange
        mock_torneo = MagicMock()
        mock_torneo.formato = 'ELIMINACION'

        # Act & Assert
        from negocio.services import generar_fixture_liga
        with pytest.raises(ValidationError, match="formato LIGA"):
            generar_fixture_liga(mock_torneo)

    def test_fixture_already_generated_raises(self):
        """Edge Case: fixture ya generado lanza ValidationError."""
        # Arrange
        mock_torneo = MagicMock()
        mock_torneo.formato = 'LIGA'
        mock_torneo.fixture_generado = True

        # Act & Assert
        from negocio.services import generar_fixture_liga
        with pytest.raises(ValidationError, match="ya ha sido generado"):
            generar_fixture_liga(mock_torneo)

    def test_less_than_two_teams_raises(self):
        """Edge Case: menos de 2 equipos lanza ValidationError."""
        # Arrange
        mock_torneo = MagicMock()
        mock_torneo.formato = 'LIGA'
        mock_torneo.fixture_generado = False
        mock_torneo.equipos.all.return_value = [MagicMock()]

        # Act & Assert
        from negocio.services import generar_fixture_liga
        with pytest.raises(ValidationError, match="al menos 2 equipos"):
            generar_fixture_liga(mock_torneo)

    @patch('negocio.services.Partido')
    @patch('negocio.services.PosicionEquipo')
    def test_two_teams_generates_one_match(self, mock_PosicionEquipo, mock_Partido):
        """Edge Case: 2 equipos genera exactamente 1 partido."""
        # Arrange
        mock_PosicionEquipo.objects.get_or_create.return_value = (MagicMock(), True)
        equipos = [MagicMock(), MagicMock()]
        mock_torneo = MagicMock()
        mock_torneo.formato = 'LIGA'
        mock_torneo.fixture_generado = False
        mock_torneo.equipos.all.return_value = equipos

        # Act
        from negocio.services import generar_fixture_liga
        result = generar_fixture_liga(mock_torneo)

        # Assert
        assert result is True
        assert mock_Partido.objects.create.call_count == 1

    @patch('negocio.services.Partido')
    @patch('negocio.services.PosicionEquipo')
    def test_odd_number_of_teams(self, mock_PosicionEquipo, mock_Partido):
        """Edge Case: número impar de equipos genera fixture con 'descansos'."""
        # Arrange
        mock_PosicionEquipo.objects.get_or_create.return_value = (MagicMock(), True)
        equipos = [MagicMock() for _ in range(3)]
        mock_torneo = MagicMock()
        mock_torneo.formato = 'LIGA'
        mock_torneo.fixture_generado = False
        mock_torneo.equipos.all.return_value = equipos

        # Act
        from negocio.services import generar_fixture_liga
        result = generar_fixture_liga(mock_torneo)

        # Assert
        assert result is True
        # 3 equipos: 3 jornadas con 1 partido real c/u = 3 partidos
        assert mock_Partido.objects.create.call_count == 3

    @patch('negocio.services.Partido')
    @patch('negocio.services.PosicionEquipo')
    def test_position_table_initialized_for_all_teams(self, mock_PosicionEquipo, mock_Partido):
        """Verifica que se inicialice la tabla de posiciones para cada equipo."""
        # Arrange
        mock_PosicionEquipo.objects.get_or_create.return_value = (MagicMock(), True)
        equipos = [MagicMock() for _ in range(4)]
        mock_torneo = MagicMock()
        mock_torneo.formato = 'LIGA'
        mock_torneo.fixture_generado = False
        mock_torneo.equipos.all.return_value = equipos

        # Act
        from negocio.services import generar_fixture_liga
        generar_fixture_liga(mock_torneo)

        # Assert
        assert mock_PosicionEquipo.objects.get_or_create.call_count == 4


class TestRegistrarResultado:
    """Pruebas para registrar_resultado."""

    @patch('negocio.services._actualizar_posiciones')
    def test_happy_path_register_result(self, mock_actualizar):
        """Happy Path: registra resultado exitosamente."""
        # Arrange
        mock_usuario = MagicMock()
        mock_partido = MagicMock()
        mock_partido.torneo.organizador = mock_usuario
        mock_partido.estado = 'PENDIENTE'

        # Act
        from negocio.services import registrar_resultado
        registrar_resultado(mock_partido, 2, 1, mock_usuario)

        # Assert
        assert mock_partido.goles_local == 2
        assert mock_partido.goles_visitante == 1
        assert mock_partido.estado == 'JUGADO'
        mock_partido.save.assert_called_once()
        mock_actualizar.assert_called_once_with(mock_partido.torneo)

    def test_non_organizer_raises(self):
        """Edge Case: usuario no organizador lanza ValidationError."""
        # Arrange
        mock_usuario = MagicMock()
        mock_otro = MagicMock()
        mock_partido = MagicMock()
        mock_partido.torneo.organizador = mock_otro
        mock_partido.estado = 'PENDIENTE'

        # Act & Assert
        from negocio.services import registrar_resultado
        with pytest.raises(ValidationError, match="organizador"):
            registrar_resultado(mock_partido, 1, 1, mock_usuario)

    def test_already_played_raises(self):
        """Edge Case: partido ya jugado lanza ValidationError."""
        # Arrange
        mock_usuario = MagicMock()
        mock_partido = MagicMock()
        mock_partido.torneo.organizador = mock_usuario
        mock_partido.estado = 'JUGADO'

        # Act & Assert
        from negocio.services import registrar_resultado
        with pytest.raises(ValidationError, match="ya cuenta con un resultado"):
            registrar_resultado(mock_partido, 0, 0, mock_usuario)

    @patch('negocio.services._actualizar_posiciones')
    def test_draw_result(self, mock_actualizar):
        """Happy Path: registra empate (0-0)."""
        # Arrange
        mock_usuario = MagicMock()
        mock_partido = MagicMock()
        mock_partido.torneo.organizador = mock_usuario
        mock_partido.estado = 'PENDIENTE'

        # Act
        from negocio.services import registrar_resultado
        registrar_resultado(mock_partido, 0, 0, mock_usuario)

        # Assert
        assert mock_partido.goles_local == 0
        assert mock_partido.goles_visitante == 0
        assert mock_partido.estado == 'JUGADO'


class TestActualizarPosiciones:
    """Pruebas para _actualizar_posiciones."""

    @patch('negocio.services.Partido')
    @patch('negocio.services.PosicionEquipo')
    def test_happy_path_local_win(self, mock_PosicionEquipo, mock_Partido):
        """Happy Path: victoria local actualiza correctamente."""
        # Arrange
        mock_torneo = MagicMock()

        mock_pos_local = MagicMock()
        mock_pos_local.equipo.id = 1
        mock_pos_local.puntos = 0
        mock_pos_local.partidos_jugados = 0
        mock_pos_local.partidos_ganados = 0
        mock_pos_local.partidos_empatados = 0
        mock_pos_local.partidos_perdidos = 0
        mock_pos_local.goles_favor = 0
        mock_pos_local.goles_contra = 0

        mock_pos_visitante = MagicMock()
        mock_pos_visitante.equipo.id = 2
        mock_pos_visitante.puntos = 0
        mock_pos_visitante.partidos_jugados = 0
        mock_pos_visitante.partidos_ganados = 0
        mock_pos_visitante.partidos_empatados = 0
        mock_pos_visitante.partidos_perdidos = 0
        mock_pos_visitante.goles_favor = 0
        mock_pos_visitante.goles_contra = 0

        # Mock iter returns the list, and mock the update method on the MagicMock returned by filter
        mock_qs = MagicMock()
        mock_qs.__iter__.return_value = [mock_pos_local, mock_pos_visitante]
        mock_qs.update = MagicMock()
        mock_PosicionEquipo.objects.filter.return_value = mock_qs

        mock_partido = MagicMock()
        mock_partido.equipo_local.id = 1
        mock_partido.equipo_visitante.id = 2
        mock_partido.goles_local = 3
        mock_partido.goles_visitante = 1
        
        mock_partido_qs = MagicMock()
        mock_partido_qs.__iter__.return_value = [mock_partido]
        mock_Partido.objects.filter.return_value = mock_partido_qs

        # Act
        from negocio.services import _actualizar_posiciones
        _actualizar_posiciones(mock_torneo)

        # Assert
        assert mock_pos_local.puntos == 3  # Victoria = 3 puntos
        assert mock_pos_local.partidos_ganados == 1
        assert mock_pos_local.goles_favor == 3
        assert mock_pos_local.goles_contra == 1
        assert mock_pos_visitante.puntos == 0
        assert mock_pos_visitante.partidos_perdidos == 1

    @patch('negocio.services.Partido')
    @patch('negocio.services.PosicionEquipo')
    def test_draw_gives_one_point_each(self, mock_PosicionEquipo, mock_Partido):
        """Happy Path: empate otorga 1 punto a cada equipo."""
        # Arrange
        mock_torneo = MagicMock()

        mock_pos_local = MagicMock()
        mock_pos_local.equipo.id = 1
        mock_pos_local.puntos = 0
        mock_pos_local.partidos_jugados = 0
        mock_pos_local.partidos_ganados = 0
        mock_pos_local.partidos_empatados = 0
        mock_pos_local.partidos_perdidos = 0
        mock_pos_local.goles_favor = 0
        mock_pos_local.goles_contra = 0

        mock_pos_visitante = MagicMock()
        mock_pos_visitante.equipo.id = 2
        mock_pos_visitante.puntos = 0
        mock_pos_visitante.partidos_jugados = 0
        mock_pos_visitante.partidos_ganados = 0
        mock_pos_visitante.partidos_empatados = 0
        mock_pos_visitante.partidos_perdidos = 0
        mock_pos_visitante.goles_favor = 0
        mock_pos_visitante.goles_contra = 0

        mock_qs = MagicMock()
        mock_qs.__iter__.return_value = [mock_pos_local, mock_pos_visitante]
        mock_qs.update = MagicMock()
        mock_PosicionEquipo.objects.filter.return_value = mock_qs

        mock_partido = MagicMock()
        mock_partido.equipo_local.id = 1
        mock_partido.equipo_visitante.id = 2
        mock_partido.goles_local = 2
        mock_partido.goles_visitante = 2
        
        mock_partido_qs = MagicMock()
        mock_partido_qs.__iter__.return_value = [mock_partido]
        mock_Partido.objects.filter.return_value = mock_partido_qs

        # Act
        from negocio.services import _actualizar_posiciones
        _actualizar_posiciones(mock_torneo)

        # Assert
        assert mock_pos_local.puntos == 1
        assert mock_pos_visitante.puntos == 1
        assert mock_pos_local.partidos_empatados == 1
        assert mock_pos_visitante.partidos_empatados == 1

    @patch('negocio.services.Partido')
    @patch('negocio.services.PosicionEquipo')
    def test_away_win(self, mock_PosicionEquipo, mock_Partido):
        """Happy Path: victoria visitante actualiza correctamente."""
        # Arrange
        mock_torneo = MagicMock()

        mock_pos_local = MagicMock()
        mock_pos_local.equipo.id = 1
        mock_pos_local.puntos = 0
        mock_pos_local.partidos_jugados = 0
        mock_pos_local.partidos_ganados = 0
        mock_pos_local.partidos_empatados = 0
        mock_pos_local.partidos_perdidos = 0
        mock_pos_local.goles_favor = 0
        mock_pos_local.goles_contra = 0

        mock_pos_visitante = MagicMock()
        mock_pos_visitante.equipo.id = 2
        mock_pos_visitante.puntos = 0
        mock_pos_visitante.partidos_jugados = 0
        mock_pos_visitante.partidos_ganados = 0
        mock_pos_visitante.partidos_empatados = 0
        mock_pos_visitante.partidos_perdidos = 0
        mock_pos_visitante.goles_favor = 0
        mock_pos_visitante.goles_contra = 0

        mock_qs = MagicMock()
        mock_qs.__iter__.return_value = [mock_pos_local, mock_pos_visitante]
        mock_qs.update = MagicMock()
        mock_PosicionEquipo.objects.filter.return_value = mock_qs

        mock_partido = MagicMock()
        mock_partido.equipo_local.id = 1
        mock_partido.equipo_visitante.id = 2
        mock_partido.goles_local = 0
        mock_partido.goles_visitante = 2
        
        mock_partido_qs = MagicMock()
        mock_partido_qs.__iter__.return_value = [mock_partido]
        mock_Partido.objects.filter.return_value = mock_partido_qs

        # Act
        from negocio.services import _actualizar_posiciones
        _actualizar_posiciones(mock_torneo)

        # Assert
        assert mock_pos_visitante.puntos == 3
        assert mock_pos_visitante.partidos_ganados == 1
        assert mock_pos_local.partidos_perdidos == 1
        assert mock_pos_local.puntos == 0

    @patch('negocio.services.Partido')
    @patch('negocio.services.PosicionEquipo')
    def test_no_played_matches(self, mock_PosicionEquipo, mock_Partido):
        """Edge Case: sin partidos jugados, posiciones quedan en reset."""
        # Arrange
        mock_torneo = MagicMock()
        
        mock_qs = MagicMock()
        mock_qs.__iter__.return_value = []
        mock_qs.update = MagicMock()
        mock_PosicionEquipo.objects.filter.return_value = mock_qs
        
        mock_partido_qs = MagicMock()
        mock_partido_qs.__iter__.return_value = []
        mock_Partido.objects.filter.return_value = mock_partido_qs

        # Act
        from negocio.services import _actualizar_posiciones
        _actualizar_posiciones(mock_torneo)

        # Assert
        mock_PosicionEquipo.objects.bulk_update.assert_called_once()
