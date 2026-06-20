"""
Pruebas unitarias para canchas/forms.py

Componentes probados:
- CanchaForm: validación de precio (positivo, límite máximo).
- DisponibilidadForm: campos y widgets.
"""
import pytest
from decimal import Decimal
from django import forms


class TestCanchaForm:
    """Pruebas del formulario CanchaForm."""

    def test_clean_precio_valid(self):
        """Happy Path: precio válido (ej. 50,000)."""
        # Arrange
        from canchas.forms import CanchaForm
        form = CanchaForm()
        form.cleaned_data = {'precio': Decimal('50000.00')}

        # Act
        result = form.clean_precio()

        # Assert
        assert result == Decimal('50000.00')

    def test_clean_precio_zero_raises(self):
        """Edge Case: precio igual a cero lanza ValidationError."""
        # Arrange
        from canchas.forms import CanchaForm
        form = CanchaForm()
        form.cleaned_data = {'precio': Decimal('0')}

        # Act & Assert
        from django.core.exceptions import ValidationError
        with pytest.raises(ValidationError, match="mayor a cero"):
            form.clean_precio()

    def test_clean_precio_negative_raises(self):
        """Edge Case: precio negativo lanza ValidationError."""
        # Arrange
        from canchas.forms import CanchaForm
        form = CanchaForm()
        form.cleaned_data = {'precio': Decimal('-100')}

        # Act & Assert
        from django.core.exceptions import ValidationError
        with pytest.raises(ValidationError, match="mayor a cero"):
            form.clean_precio()

    def test_clean_precio_over_million_raises(self):
        """Edge Case: precio superior a 1,000,000 lanza ValidationError."""
        # Arrange
        from canchas.forms import CanchaForm
        form = CanchaForm()
        form.cleaned_data = {'precio': Decimal('1000001')}

        # Act & Assert
        from django.core.exceptions import ValidationError
        with pytest.raises(ValidationError, match="1,000,000"):
            form.clean_precio()

    def test_clean_precio_exactly_million_passes(self):
        """Edge Case: precio exactamente 1,000,000 es válido."""
        # Arrange
        from canchas.forms import CanchaForm
        form = CanchaForm()
        form.cleaned_data = {'precio': Decimal('1000000')}

        # Act
        result = form.clean_precio()

        # Assert
        assert result == Decimal('1000000')

    def test_clean_precio_none_returns_none(self):
        """Edge Case: precio None retorna None."""
        # Arrange
        from canchas.forms import CanchaForm
        form = CanchaForm()
        form.cleaned_data = {'precio': None}

        # Act
        result = form.clean_precio()

        # Assert
        assert result is None

    def test_clean_precio_one_cent_valid(self):
        """Edge Case: precio mínimo válido (0.01)."""
        # Arrange
        from canchas.forms import CanchaForm
        form = CanchaForm()
        form.cleaned_data = {'precio': Decimal('0.01')}

        # Act
        result = form.clean_precio()

        # Assert
        assert result == Decimal('0.01')

    def test_form_excludes_dueno_field(self):
        """Verifica que el campo dueño no esté en los campos del form."""
        # Arrange & Act
        from canchas.forms import CanchaForm

        # Assert
        assert 'dueño' not in CanchaForm.Meta.fields

    def test_form_includes_expected_fields(self):
        """Verifica que incluya todos los campos esperados."""
        # Arrange & Act
        from canchas.forms import CanchaForm

        # Assert
        expected = ['nombre', 'descripcion', 'precio', 'ubicacion', 'imagen', 'deporte']
        assert CanchaForm.Meta.fields == expected


class TestDisponibilidadForm:
    """Pruebas del formulario DisponibilidadForm."""

    def test_form_fields(self):
        """Verifica los campos del formulario."""
        # Arrange & Act
        from canchas.forms import DisponibilidadForm

        # Assert
        assert DisponibilidadForm.Meta.fields == ['dia_semana', 'hora_inicio', 'hora_fin']

    def test_hora_widgets_are_time_inputs(self):
        """Verifica que los widgets de hora sean de tipo TimeInput."""
        # Arrange & Act
        from canchas.forms import DisponibilidadForm

        # Assert
        widgets = DisponibilidadForm.Meta.widgets
        assert isinstance(widgets['hora_inicio'], forms.TimeInput)
        assert isinstance(widgets['hora_fin'], forms.TimeInput)
