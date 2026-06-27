"""
Pruebas unitarias para negocio/forms.py

Componentes probados:
- TorneoForm: campos y widgets.
- EquipoForm: campos y widgets.
"""
import pytest
from django import forms


class TestTorneoForm:
    """Pruebas del formulario TorneoForm."""

    def test_form_fields(self):
        """Verifica que incluya los campos esperados."""
        # Arrange & Act
        from negocio.forms import TorneoForm

        # Assert
        expected_fields = [
            'nombre', 'descripcion', 'fecha_inicio', 'fecha_fin',
            'deporte', 'canchas', 'max_equipos', 'formato'
        ]
        assert TorneoForm.Meta.fields == expected_fields

    def test_fecha_inicio_widget_is_date(self):
        """Verifica que fecha_inicio use widget tipo DateInput."""
        # Arrange & Act
        from negocio.forms import TorneoForm
        widgets = TorneoForm.Meta.widgets

        # Assert
        assert isinstance(widgets['fecha_inicio'], forms.DateInput)

    def test_fecha_fin_widget_is_date(self):
        """Verifica que fecha_fin use widget tipo DateInput."""
        # Arrange & Act
        from negocio.forms import TorneoForm
        widgets = TorneoForm.Meta.widgets

        # Assert
        assert isinstance(widgets['fecha_fin'], forms.DateInput)

    def test_form_does_not_include_estado(self):
        """Edge Case: el formulario NO incluye campo 'estado' (se maneja en backend)."""
        # Arrange & Act
        from negocio.forms import TorneoForm

        # Assert
        assert 'estado' not in TorneoForm.Meta.fields

    def test_form_does_not_include_organizador(self):
        """Edge Case: el formulario NO incluye campo 'organizador' (se asigna automáticamente)."""
        # Arrange & Act
        from negocio.forms import TorneoForm

        # Assert
        assert 'organizador' not in TorneoForm.Meta.fields


class TestEquipoForm:
    """Pruebas del formulario EquipoForm."""

    def test_form_fields(self):
        """Verifica que incluya los campos esperados."""
        # Arrange & Act
        from negocio.forms import EquipoForm

        # Assert
        expected_fields = ['nombre', 'logo', 'jugadores']
        assert EquipoForm.Meta.fields == expected_fields

    def test_nombre_widget_is_text_input(self):
        """Verifica que nombre use widget TextInput."""
        # Arrange & Act
        from negocio.forms import EquipoForm
        widgets = EquipoForm.Meta.widgets

        # Assert
        assert 'nombre' in widgets

    def test_jugadores_widget_is_select_multiple(self):
        """Verifica que jugadores use widget SelectMultiple."""
        # Arrange & Act
        from negocio.forms import EquipoForm
        widgets = EquipoForm.Meta.widgets

        # Assert
        assert 'jugadores' in widgets
