"""
Pruebas unitarias para usuarios/forms.py

Componentes probados:
- RegistroUsuarioForm: formulario de registro con validaciones de nombre, email.
- PerfilForm: formulario de edición de perfil con validación de unicidad de email.
"""
import pytest
from unittest.mock import patch, MagicMock
from usuarios.forms import RegistroUsuarioForm, PerfilForm


class TestRegistroUsuarioForm:
    """Pruebas del formulario de registro de usuarios."""

    def test_clean_first_name_valid(self):
        """Happy Path: nombre sin caracteres especiales ni números."""
        # Arrange
        form = RegistroUsuarioForm()
        form.cleaned_data = {'first_name': 'Carlos'}

        # Act
        result = form.clean_first_name()

        # Assert
        assert result == 'Carlos'

    def test_clean_first_name_with_numbers_raises(self):
        """Edge Case: nombre con números debe fallar."""
        # Arrange
        form = RegistroUsuarioForm()
        form.cleaned_data = {'first_name': 'Carlos123'}

        # Act & Assert
        from django.core.exceptions import ValidationError
        with pytest.raises(ValidationError):
            form.clean_first_name()

    def test_clean_first_name_with_special_chars_raises(self):
        """Edge Case: nombre con caracteres especiales debe fallar."""
        # Arrange
        form = RegistroUsuarioForm()
        form.cleaned_data = {'first_name': 'Carlos@!'}

        # Act & Assert
        from django.core.exceptions import ValidationError
        with pytest.raises(ValidationError):
            form.clean_first_name()

    def test_clean_last_name_valid(self):
        """Happy Path: apellido válido."""
        # Arrange
        form = RegistroUsuarioForm()
        form.cleaned_data = {'last_name': 'González'}

        # Act
        result = form.clean_last_name()

        # Assert
        assert result == 'González'

    def test_clean_last_name_with_numbers_raises(self):
        """Edge Case: apellido con números debe fallar."""
        # Arrange
        form = RegistroUsuarioForm()
        form.cleaned_data = {'last_name': 'Gomez99'}

        # Act & Assert
        from django.core.exceptions import ValidationError
        with pytest.raises(ValidationError):
            form.clean_last_name()

    @patch('usuarios.forms.CustomUser.objects')
    def test_clean_email_valid_unique(self, mock_objects):
        """Happy Path: email válido y único."""
        # Arrange
        mock_objects.filter.return_value.exists.return_value = False
        form = RegistroUsuarioForm()
        form.cleaned_data = {'email': 'carlos@example.com'}

        # Act
        result = form.clean_email()

        # Assert
        assert result == 'carlos@example.com'

    @patch('usuarios.forms.CustomUser.objects')
    def test_clean_email_already_registered_raises(self, mock_objects):
        """Edge Case: email ya registrado debe fallar."""
        # Arrange
        mock_objects.filter.return_value.exists.return_value = True
        form = RegistroUsuarioForm()
        form.cleaned_data = {'email': 'existing@example.com'}

        # Act & Assert
        from django.core.exceptions import ValidationError
        with pytest.raises(ValidationError, match='ya está registrado'):
            form.clean_email()

    def test_clean_email_invalid_format_raises(self):
        """Edge Case: formato de email inválido."""
        # Arrange
        form = RegistroUsuarioForm()
        form.cleaned_data = {'email': 'not-an-email'}

        # Act & Assert
        from django.core.exceptions import ValidationError
        with pytest.raises(ValidationError, match='válido'):
            form.clean_email()

    def test_clean_first_name_empty_string(self):
        """Edge Case: nombre vacío."""
        # Arrange
        form = RegistroUsuarioForm()
        form.cleaned_data = {'first_name': ''}

        # Act
        result = form.clean_first_name()

        # Assert  — vacío pasa la regex, Required es manejado por el campo
        assert result == ''

    def test_clean_first_name_with_accents(self):
        """Happy Path: nombre con acentos (español)."""
        # Arrange
        form = RegistroUsuarioForm()
        form.cleaned_data = {'first_name': 'José María'}

        # Act
        result = form.clean_first_name()

        # Assert
        assert result == 'José María'


class TestPerfilForm:
    """Pruebas del formulario de edición de perfil."""

    def test_clean_first_name_valid(self):
        """Happy Path: nombre válido en edición de perfil."""
        # Arrange
        form = PerfilForm()
        form.cleaned_data = {'first_name': 'Andrés'}

        # Act
        result = form.clean_first_name()

        # Assert
        assert result == 'Andrés'

    def test_clean_first_name_with_number_raises(self):
        """Edge Case: nombre con números en edición de perfil."""
        # Arrange
        form = PerfilForm()
        form.cleaned_data = {'first_name': 'Andrés2'}

        # Act & Assert
        from django.core.exceptions import ValidationError
        with pytest.raises(ValidationError):
            form.clean_first_name()

    def test_clean_last_name_valid(self):
        """Happy Path: apellido válido en edición de perfil."""
        # Arrange
        form = PerfilForm()
        form.cleaned_data = {'last_name': 'Ramírez'}

        # Act
        result = form.clean_last_name()

        # Assert
        assert result == 'Ramírez'

    def test_clean_last_name_with_special_chars_raises(self):
        """Edge Case: apellido con caracteres especiales."""
        # Arrange
        form = PerfilForm()
        form.cleaned_data = {'last_name': 'López#1'}

        # Act & Assert
        from django.core.exceptions import ValidationError
        with pytest.raises(ValidationError):
            form.clean_last_name()

    @patch('usuarios.forms.CustomUser.objects')
    def test_clean_email_unique_for_other_users(self, mock_objects):
        """Happy Path: email que no pertenece a otro usuario."""
        # Arrange
        mock_objects.filter.return_value.exclude.return_value.exists.return_value = False
        form = PerfilForm()
        form.instance = MagicMock()
        form.instance.pk = 1
        form.cleaned_data = {'email': 'nuevo@example.com'}

        # Act
        result = form.clean_email()

        # Assert
        assert result == 'nuevo@example.com'

    @patch('usuarios.forms.CustomUser.objects')
    def test_clean_email_duplicate_for_other_user_raises(self, mock_objects):
        """Edge Case: email que ya usa OTRO usuario."""
        # Arrange
        mock_objects.filter.return_value.exclude.return_value.exists.return_value = True
        form = PerfilForm()
        form.instance = MagicMock()
        form.instance.pk = 1
        form.cleaned_data = {'email': 'taken@example.com'}

        # Act & Assert
        from django.core.exceptions import ValidationError
        with pytest.raises(ValidationError, match='ya está en uso'):
            form.clean_email()

    def test_clean_email_invalid_format_raises(self):
        """Edge Case: formato de email inválido en edición."""
        # Arrange
        form = PerfilForm()
        form.instance = MagicMock()
        form.instance.pk = 1
        form.cleaned_data = {'email': 'bad-format'}

        # Act & Assert
        from django.core.exceptions import ValidationError
        with pytest.raises(ValidationError, match='válido'):
            form.clean_email()
