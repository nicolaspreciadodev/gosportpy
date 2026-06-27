"""
Pruebas unitarias para core/emails.py

Componentes probados:
- enviar_email_base: envío de email con HTML y texto plano.
- enviar_confirmacion_reserva: doble envío (deportista + dueño).
- enviar_recordatorio_reserva: envío de recordatorio.
- enviar_notificacion_inscripcion_equipo: notificación al organizador.
- enviar_notificacion_torneo_aprobado: notificación de aprobación.
"""
import pytest
from unittest.mock import MagicMock, patch, call


class TestEnviarEmailBase:
    """Pruebas para enviar_email_base."""

    @patch('core.emails.EmailMultiAlternatives')
    @patch('core.emails.strip_tags')
    @patch('core.emails.render_to_string')
    @patch('core.emails.settings')
    def test_happy_path_sends_email(self, mock_settings, mock_render, mock_strip, mock_email_class):
        """Happy Path: envía email correctamente."""
        # Arrange
        mock_settings.DEFAULT_FROM_EMAIL = 'noreply@gosport.com'
        mock_render.return_value = '<h1>Hola</h1>'
        mock_strip.return_value = 'Hola'
        mock_email_instance = MagicMock()
        mock_email_class.return_value = mock_email_instance

        # Act
        from core.emails import enviar_email_base
        enviar_email_base(
            subject='Test Subject',
            context={'key': 'value'},
            template_name='emails/test.html',
            to_emails=['user@example.com']
        )

        # Assert
        mock_render.assert_called_once_with('emails/test.html', {'key': 'value'})
        mock_email_class.assert_called_once()
        mock_email_instance.attach_alternative.assert_called_once_with('<h1>Hola</h1>', 'text/html')
        mock_email_instance.send.assert_called_once_with(fail_silently=False)

    @patch('core.emails.EmailMultiAlternatives')
    @patch('core.emails.strip_tags')
    @patch('core.emails.render_to_string')
    @patch('core.emails.settings')
    def test_email_has_text_fallback(self, mock_settings, mock_render, mock_strip, mock_email_class):
        """Verifica que el email incluya fallback a texto plano."""
        # Arrange
        mock_settings.DEFAULT_FROM_EMAIL = 'noreply@gosport.com'
        mock_render.return_value = '<p>Contenido HTML</p>'
        mock_strip.return_value = 'Contenido HTML'
        mock_email_instance = MagicMock()
        mock_email_class.return_value = mock_email_instance

        # Act
        from core.emails import enviar_email_base
        enviar_email_base('Subject', {}, 'template.html', ['a@b.com'])

        # Assert
        call_kwargs = mock_email_class.call_args[1]
        assert call_kwargs['body'] == 'Contenido HTML'

    @patch('core.emails.EmailMultiAlternatives')
    @patch('core.emails.strip_tags')
    @patch('core.emails.render_to_string')
    @patch('core.emails.settings')
    def test_email_uses_correct_from_email(self, mock_settings, mock_render, mock_strip, mock_email_class):
        """Verifica que use DEFAULT_FROM_EMAIL como remitente."""
        # Arrange
        mock_settings.DEFAULT_FROM_EMAIL = 'custom@gosport.com'
        mock_render.return_value = '<p>Hi</p>'
        mock_strip.return_value = 'Hi'
        mock_email_instance = MagicMock()
        mock_email_class.return_value = mock_email_instance

        # Act
        from core.emails import enviar_email_base
        enviar_email_base('Sub', {}, 'tpl.html', ['a@b.com'])

        # Assert
        call_kwargs = mock_email_class.call_args[1]
        assert call_kwargs['from_email'] == 'custom@gosport.com'


class TestEnviarConfirmacionReserva:
    """Pruebas para enviar_confirmacion_reserva."""

    @patch('core.emails.enviar_email_base')
    def test_happy_path_sends_two_emails(self, mock_enviar):
        """Happy Path: envía 2 emails (deportista + dueño)."""
        # Arrange
        mock_reserva = MagicMock()
        mock_reserva.cancha.nombre = "Cancha Central"
        mock_reserva.usuario.email = "deportista@test.com"
        mock_reserva.cancha.dueño.email = "dueno@test.com"

        # Act
        from core.emails import enviar_confirmacion_reserva
        enviar_confirmacion_reserva(mock_reserva)

        # Assert
        assert mock_enviar.call_count == 2

    @patch('core.emails.enviar_email_base')
    def test_deportista_receives_confirmation(self, mock_enviar):
        """Verifica que el deportista reciba el email de confirmación."""
        # Arrange
        mock_reserva = MagicMock()
        mock_reserva.cancha.nombre = "Cancha Central"
        mock_reserva.usuario.email = "deportista@test.com"
        mock_reserva.cancha.dueño.email = "dueno@test.com"

        # Act
        from core.emails import enviar_confirmacion_reserva
        enviar_confirmacion_reserva(mock_reserva)

        # Assert
        first_call = mock_enviar.call_args_list[0]
        assert first_call[1]['to_emails'] == ["deportista@test.com"]
        assert "Confirmación" in first_call[1]['subject']

    @patch('core.emails.enviar_email_base')
    def test_dueno_receives_notification(self, mock_enviar):
        """Verifica que el dueño reciba notificación de nueva reserva."""
        # Arrange
        mock_reserva = MagicMock()
        mock_reserva.cancha.nombre = "Cancha Central"
        mock_reserva.usuario.email = "deportista@test.com"
        mock_reserva.cancha.dueño.email = "dueno@test.com"

        # Act
        from core.emails import enviar_confirmacion_reserva
        enviar_confirmacion_reserva(mock_reserva)

        # Assert
        second_call = mock_enviar.call_args_list[1]
        assert second_call[1]['to_emails'] == ["dueno@test.com"]
        assert "Nueva Reserva" in second_call[1]['subject']


class TestEnviarRecordatorioReserva:
    """Pruebas para enviar_recordatorio_reserva."""

    @patch('core.emails.enviar_email_base')
    def test_happy_path_sends_reminder(self, mock_enviar):
        """Happy Path: envía recordatorio al deportista."""
        # Arrange
        mock_reserva = MagicMock()
        mock_reserva.cancha.nombre = "Cancha Este"
        mock_reserva.usuario.email = "user@test.com"

        # Act
        from core.emails import enviar_recordatorio_reserva
        enviar_recordatorio_reserva(mock_reserva)

        # Assert
        mock_enviar.assert_called_once()
        call_kwargs = mock_enviar.call_args[1]
        assert call_kwargs['to_emails'] == ["user@test.com"]
        assert "Recordatorio" in call_kwargs['subject']


class TestEnviarNotificacionInscripcionEquipo:
    """Pruebas para enviar_notificacion_inscripcion_equipo."""

    @patch('core.emails.enviar_email_base')
    def test_happy_path_notifies_organizer(self, mock_enviar):
        """Happy Path: notifica al organizador del torneo."""
        # Arrange
        mock_torneo = MagicMock()
        mock_torneo.nombre = "Copa Primavera"
        mock_torneo.organizador.email = "org@test.com"
        mock_equipo = MagicMock()

        # Act
        from core.emails import enviar_notificacion_inscripcion_equipo
        enviar_notificacion_inscripcion_equipo(mock_torneo, mock_equipo)

        # Assert
        mock_enviar.assert_called_once()
        call_kwargs = mock_enviar.call_args[1]
        assert call_kwargs['to_emails'] == ["org@test.com"]
        assert "Equipo Inscrito" in call_kwargs['subject']


class TestEnviarNotificacionTorneoAprobado:
    """Pruebas para enviar_notificacion_torneo_aprobado."""

    @patch('core.emails.enviar_email_base')
    def test_happy_path_notifies_organizer_approval(self, mock_enviar):
        """Happy Path: notifica al organizador que su torneo fue aprobado."""
        # Arrange
        mock_torneo = MagicMock()
        mock_torneo.nombre = "Liga Nacional"
        mock_torneo.organizador.email = "org@test.com"

        # Act
        from core.emails import enviar_notificacion_torneo_aprobado
        enviar_notificacion_torneo_aprobado(mock_torneo)

        # Assert
        mock_enviar.assert_called_once()
        call_kwargs = mock_enviar.call_args[1]
        assert call_kwargs['to_emails'] == ["org@test.com"]
        assert "Aprobado" in call_kwargs['subject']

    @patch('core.emails.enviar_email_base')
    def test_email_context_includes_torneo_and_organizer(self, mock_enviar):
        """Verifica que el contexto incluya torneo y organizador."""
        # Arrange
        mock_torneo = MagicMock()
        mock_torneo.nombre = "Liga Nacional"
        mock_torneo.organizador.email = "org@test.com"

        # Act
        from core.emails import enviar_notificacion_torneo_aprobado
        enviar_notificacion_torneo_aprobado(mock_torneo)

        # Assert
        call_kwargs = mock_enviar.call_args[1]
        context = call_kwargs['context']
        assert 'torneo' in context
        assert 'organizador' in context
