# usuarios/forms.py
"""Formulario de registro de nuevos usuarios de GoSport."""
import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, SolicitudRolDueño


class RegistroUsuarioForm(UserCreationForm):
    """Extiende UserCreationForm para el registro público.

    El campo 'rol' NO se expone: todos los usuarios nuevos se registran
    automáticamente como 'DEPORTISTA'. Para convertirse en Dueño de Cancha
    deben enviar una solicitud que el SuperAdmin aprueba.
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

    def save(self, commit=True):
        """Guarda el usuario con el rol seleccionado."""
        user = super().save(commit=False)
        if commit:
            user.save()
        return user

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name', '')
        if re.search(r'[0-9!@#\$%\^&\*\(\)_\+\-\=\[\]\{\};:\'",<>\.\?\/\\|]', first_name):
            raise forms.ValidationError('El nombre no debe contener números ni caracteres especiales.')
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name', '')
        if re.search(r'[0-9!@#\$%\^&\*\(\)_\+\-\=\[\]\{\};:\'",<>\.\?\/\\|]', last_name):
            raise forms.ValidationError('El apellido no debe contener números ni caracteres especiales.')
        return last_name

    def clean_email(self):
        """Valida formato y unicidad explícita."""
        email = self.cleaned_data.get('email', '').lower()
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
            raise forms.ValidationError('Ingresa un correo electrónico válido (ejemplo: usuario@dominio.com).')
        
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('Este correo ya está registrado en la plataforma.')
        return email


class PerfilForm(forms.ModelForm):
    """Formulario para la edición del perfil de usuario expuesto.

    Permite editar: nombre, apellido, email (con validación de unicidad).
    """

    first_name = forms.CharField(
        max_length=150,
        required=True,
        label='Nombre',
        widget=forms.TextInput(attrs={'class': 'form-input'})
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label='Apellido',
        widget=forms.TextInput(attrs={'class': 'form-input'})
    )
    email = forms.EmailField(
        required=True,
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-input'})
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email']

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name', '')
        if re.search(r'[0-9!@#\$%\^&\*\(\)_\+\-\=\[\]\{\};:\'",<>\.\?\/\\|]', first_name):
            raise forms.ValidationError('El nombre no debe contener números ni caracteres especiales.')
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name', '')
        if re.search(r'[0-9!@#\$%\^&\*\(\)_\+\-\=\[\]\{\};:\'",<>\.\?\/\\|]', last_name):
            raise forms.ValidationError('El apellido no debe contener números ni caracteres especiales.')
        return last_name

    def clean_email(self):
        """Valida que el nuevo email sea correcto y no pertenezca a OTRO usuario."""
        email = self.cleaned_data.get('email', '').lower()
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
            raise forms.ValidationError('Ingresa un correo electrónico válido (ejemplo: usuario@dominio.com).')
            
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Este correo ya está en uso por otra cuenta.')
        return email


class SolicitudRolDueñoForm(forms.ModelForm):
    """Formulario para que un Deportista solicite el rol de Dueño de Cancha."""

    motivo = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'rows': 5,
            'placeholder': 'Cuéntanos brevemente tu establecimiento, dirección aproximada y por qué deseas ser parte de GoSport como Dueño de Cancha...',
        }),
        label='Motivo de la solicitud',
        min_length=30,
        max_length=1000,
        error_messages={
            'min_length': 'El motivo debe tener al menos 30 caracteres.',
            'max_length': 'El motivo no puede superar los 1000 caracteres.',
        }
    )

    class Meta:
        model = SolicitudRolDueño
        fields = ['motivo']
