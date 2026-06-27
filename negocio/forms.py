from django import forms
from .models import Torneo, Equipo

class TorneoForm(forms.ModelForm):
    class Meta:
        model = Torneo
        fields = ['nombre', 'descripcion', 'fecha_inicio', 'fecha_fin', 'deporte', 'canchas', 'max_equipos', 'formato']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2 text-white'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2 text-white'}),
            'nombre': forms.TextInput(attrs={'class': 'w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2 text-white'}),
            'descripcion': forms.Textarea(attrs={'class': 'w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2 text-white', 'rows': 3}),
            'deporte': forms.Select(attrs={'class': 'w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2 text-white'}),
            'canchas': forms.SelectMultiple(attrs={'class': 'w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2 text-white'}),
            'max_equipos': forms.NumberInput(attrs={'class': 'w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2 text-white'}),
            'formato': forms.Select(attrs={'class': 'w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2 text-white'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        max_equipos = cleaned_data.get('max_equipos')

        if fecha_inicio and fecha_fin:
            if fecha_fin < fecha_inicio:
                self.add_error('fecha_fin', 'La fecha de fin no puede ser anterior a la fecha de inicio.')
        
        if max_equipos is not None and max_equipos < 2:
            self.add_error('max_equipos', 'Un torneo debe permitir al menos 2 equipos.')

        return cleaned_data

class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        fields = ['nombre', 'logo', 'jugadores']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2 text-white'}),
            'logo': forms.FileInput(attrs={'class': 'w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2 text-white'}),
            'jugadores': forms.SelectMultiple(attrs={'class': 'w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2 text-white'}),
        }
