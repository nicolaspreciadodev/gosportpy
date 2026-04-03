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

class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        fields = ['nombre', 'logo', 'jugadores']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2 text-white'}),
            'logo': forms.FileInput(attrs={'class': 'w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2 text-white'}),
            'jugadores': forms.SelectMultiple(attrs={'class': 'w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2 text-white'}),
        }
