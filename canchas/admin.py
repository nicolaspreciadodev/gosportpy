from django.contrib import admin
from .models import Cancha, Deporte, Disponibilidad

@admin.register(Deporte)
class DeporteAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

@admin.register(Cancha)
class CanchaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'deporte', 'precio', 'dueño')
    list_filter = ('deporte', 'dueño')
    search_fields = ('nombre', 'ubicacion')

@admin.register(Disponibilidad)
class DisponibilidadAdmin(admin.ModelAdmin):
    list_display = ('cancha', 'dia_semana', 'hora_inicio', 'hora_fin')
    list_filter = ('cancha', 'dia_semana')
