# canchas/forms.py
"""Formulario de Cancha con validaciones de negocio."""
from django import forms
from .models import Cancha


class CanchaForm(forms.ModelForm):
    """Form para crear y editar canchas.

    Excluye el campo `dueño` ya que se asigna programáticamente
    en el service layer, evitando manipulación desde el cliente.
    """

    class Meta:
        model = Cancha
        fields = ['nombre', 'descripcion', 'precio', 'ubicacion', 'imagen', 'deporte']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_precio(self):
        """Valida que el precio sea positivo y razonable.

        Returns:
            Decimal: precio validado.

        Raises:
            ValidationError: Si el precio es <= 0 o > 1,000,000.
        """
        precio = self.cleaned_data.get('precio')
        if precio is not None:
            if precio <= 0:
                raise forms.ValidationError("El precio debe ser mayor a cero.")
            if precio > 1_000_000:
                raise forms.ValidationError("El precio no puede superar $1,000,000.")
        return precio
