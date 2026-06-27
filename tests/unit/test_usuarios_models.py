"""
Pruebas unitarias para usuarios/models.py

Componente probado: CustomUser (modelo de usuario personalizado).
Se prueban propiedades, representación en string y roles por defecto.
"""
import pytest
from unittest.mock import MagicMock


class TestCustomUserModel:
    """Pruebas del modelo CustomUser."""

    def test_str_representation_deportista(self):
        """Verifica __str__ para un deportista."""
        # Arrange
        user = MagicMock()
        user.username = "carlos99"
        user.get_rol_display.return_value = "Deportista"

        # Act
        from usuarios.models import CustomUser
        result = CustomUser.__str__(user)

        # Assert
        assert result == "carlos99 (Deportista)"

    def test_str_representation_dueno(self):
        """Verifica __str__ para un dueño de cancha."""
        # Arrange
        user = MagicMock()
        user.username = "maria_campos"
        user.get_rol_display.return_value = "Dueño de Cancha"

        # Act
        from usuarios.models import CustomUser
        result = CustomUser.__str__(user)

        # Assert
        assert result == "maria_campos (Dueño de Cancha)"

    def test_default_rol_is_deportista(self):
        """Verifica que el rol por defecto sea DEPORTISTA."""
        # Arrange & Act
        from usuarios.models import CustomUser
        field = CustomUser._meta.get_field('rol')

        # Assert
        assert field.default == 'DEPORTISTA'

    def test_role_choices_are_correct(self):
        """Verifica que los choices del rol sean los esperados."""
        # Arrange & Act
        from usuarios.models import CustomUser
        field = CustomUser._meta.get_field('rol')

        # Assert
        expected_tuple = (('DUEÑO', 'Dueño de Cancha'), ('DEPORTISTA', 'Deportista'))
        expected_list = [('DUEÑO', 'Dueño de Cancha'), ('DEPORTISTA', 'Deportista')]
        # Dependiendo de la versión de Django, choices puede ser tupla o lista
        assert field.choices == expected_tuple or field.choices == expected_list

    def test_avatar_field_is_optional(self):
        """Verifica que el avatar sea un campo opcional."""
        # Arrange & Act
        from usuarios.models import CustomUser
        field = CustomUser._meta.get_field('avatar')

        # Assert
        assert field.null is True
        assert field.blank is True

    def test_avatar_upload_to(self):
        """Verifica la ruta de subida del avatar."""
        # Arrange & Act
        from usuarios.models import CustomUser
        field = CustomUser._meta.get_field('avatar')

        # Assert
        assert field.upload_to == 'avatars/'
