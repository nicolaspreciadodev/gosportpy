"""
Pruebas unitarias para negocio/signals.py

Componente probado:
- crear_factura_reserva: signal que crea Factura automáticamente al crear Reserva.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestCrearFacturaReservaSignal:
    """Pruebas del signal crear_factura_reserva."""

    @patch('negocio.signals.Factura')
    def test_happy_path_creates_factura_on_new_reserva(self, mock_Factura):
        """Happy Path: al crear una Reserva nueva, se crea una Factura."""
        # Arrange
        mock_instance = MagicMock()
        mock_instance.cancha.precio = 100000.00

        # Act
        from negocio.signals import crear_factura_reserva
        crear_factura_reserva(
            sender=MagicMock(),
            instance=mock_instance,
            created=True
        )

        # Assert
        mock_Factura.objects.create.assert_called_once_with(
            reserva=mock_instance,
            total=100000.00
        )

    @patch('negocio.signals.Factura')
    def test_does_not_create_factura_on_update(self, mock_Factura):
        """Edge Case: NO crea Factura cuando la Reserva es actualizada (no nueva)."""
        # Arrange
        mock_instance = MagicMock()
        mock_instance.cancha.precio = 50000.00

        # Act
        from negocio.signals import crear_factura_reserva
        crear_factura_reserva(
            sender=MagicMock(),
            instance=mock_instance,
            created=False
        )

        # Assert
        mock_Factura.objects.create.assert_not_called()

    @patch('negocio.signals.Factura')
    def test_factura_total_matches_cancha_price(self, mock_Factura):
        """Verifica que el total de la factura sea el precio de la cancha."""
        # Arrange
        mock_instance = MagicMock()
        mock_instance.cancha.precio = 75000.00

        # Act
        from negocio.signals import crear_factura_reserva
        crear_factura_reserva(
            sender=MagicMock(),
            instance=mock_instance,
            created=True
        )

        # Assert
        call_kwargs = mock_Factura.objects.create.call_args[1]
        assert call_kwargs['total'] == 75000.00
        assert call_kwargs['reserva'] == mock_instance
