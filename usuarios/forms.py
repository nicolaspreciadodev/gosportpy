# usuarios/forms.py
"""Formulario de registro de nuevos usuarios de GoSport."""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class RegistroUsuarioForm(UserCreationForm):
    """Extiende UserCreationForm añadiendo campos de nombre y rol.

    Excluye campos sensibles como is_staff e is_superuser.
    El campo rol presenta solo las opciones válidas para registro público.
    """

    first_name = forms.CharField(
        max_length=150,
        required=True,
        label='Nombre',
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label='Apellido',
    )
    email = forms.EmailField(
        required=True,
        label='Correo electrónico',
    )

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'rol',
            'password1',
            'password2',
        ]

    def clean_email(self):
        """Valida que el email no esté ya registrado.

        Returns:
            str: email validado y en minúsculas.

        Raises:
            ValidationError: Si el email ya existe en la base de datos.
        """
        email = self.cleaned_data.get('email', '').lower()
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('Este correo ya está registrado.')
        return email


class PerfilForm(forms.ModelForm):
    """Formulario para la edición del perfil de usuario expuesto."""

    first_name = forms.CharField(max_length=150, required=True, label='Nombre')
    last_name = forms.CharField(max_length=150, required=True, label='Apellido')
    email = forms.EmailField(required=True, label='Correo electrónico')

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email']

    def clean_email(self):
        """Valida que el nuevo email no pertenezca a OTRO usuario.

        Returns:
            str: email validado.

        Raises:
            ValidationError: Si el email ya está en uso por otra cuenta.
        """
        email = self.cleaned_data.get('email', '').lower()
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Este correo ya está en uso por otra cuenta.')
        return email
