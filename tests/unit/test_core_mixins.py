"""
Pruebas unitarias para core/mixins.py

Componente probado:
- RoleRequiredMixin: mixin de control de acceso basado en rol.
"""
import pytest
from unittest.mock import MagicMock
from django.core.exceptions import PermissionDenied
from core.mixins import RoleRequiredMixin


class DummyBase:
    """Clase base que provee dispatch para simular a View."""
    def dispatch(self, request, *args, **kwargs):
        return "Success"


class DummyView(RoleRequiredMixin, DummyBase):
    """Vista dummy para probar el mixin de forma aislada."""
    allowed_roles = ['DUEÑO']


class DummyMultipleRolesView(RoleRequiredMixin, DummyBase):
    """Vista dummy para probar múltiples roles."""
    allowed_roles = ['DUEÑO', 'DEPORTISTA']


class TestRoleRequiredMixin:
    """Pruebas del mixin RoleRequiredMixin."""

    def test_happy_path_authenticated_user_with_allowed_role(self):
        """Happy Path: usuario autenticado con rol permitido pasa."""
        # Arrange
        view = DummyView()
        
        mock_request = MagicMock()
        mock_request.user.is_authenticated = True
        mock_request.user.rol = 'DUEÑO'

        # Act
        result = view.dispatch(mock_request)
        
        # Assert
        assert result == "Success"

    def test_unauthenticated_user_redirects(self):
        """Edge Case: usuario no autenticado se redirige."""
        # Arrange
        view = DummyView()
        mock_request = MagicMock()
        mock_request.user.is_authenticated = False

        mock_redirect = MagicMock()
        view.handle_no_permission = MagicMock(return_value=mock_redirect)

        # Act
        result = view.dispatch(mock_request)

        # Assert
        view.handle_no_permission.assert_called_once()
        assert result == mock_redirect

    def test_wrong_role_raises_permission_denied(self):
        """Edge Case: usuario con rol incorrecto lanza PermissionDenied."""
        # Arrange
        view = DummyView()

        mock_request = MagicMock()
        mock_request.user.is_authenticated = True
        mock_request.user.rol = 'DEPORTISTA'

        # Act & Assert
        with pytest.raises(PermissionDenied, match="No tienes permisos"):
            view.dispatch(mock_request)

    def test_empty_allowed_roles_denies_all(self):
        """Edge Case: sin roles permitidos, todos los usuarios son denegados."""
        # Arrange
        view = DummyView()
        view.allowed_roles = []

        mock_request = MagicMock()
        mock_request.user.is_authenticated = True
        mock_request.user.rol = 'DUEÑO'

        # Act & Assert
        with pytest.raises(PermissionDenied):
            view.dispatch(mock_request)

    def test_multiple_allowed_roles(self):
        """Happy Path: usuario con uno de los múltiples roles permitidos."""
        # Arrange
        view = DummyMultipleRolesView()

        mock_request = MagicMock()
        mock_request.user.is_authenticated = True
        mock_request.user.rol = 'DEPORTISTA'

        # Act
        result = view.dispatch(mock_request)

        # Assert
        assert result == "Success"

    def test_default_allowed_roles_is_empty(self):
        """Verifica que allowed_roles por defecto sea una lista vacía."""
        # Arrange & Act
        from core.mixins import RoleRequiredMixin

        # Assert
        assert RoleRequiredMixin.allowed_roles == []
