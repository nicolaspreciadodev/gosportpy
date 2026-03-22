from django.db import models
from django.conf import settings

class Deporte(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.nombre

class Cancha(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    ubicacion = models.CharField(max_length=255)
    imagen = models.ImageField(upload_to='canchas/', blank=True, null=True)
    dueño = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='canchas')
    deporte = models.ForeignKey(Deporte, on_delete=models.SET_NULL, null=True, related_name='canchas')
    
    def __str__(self):
        return self.nombre

class Disponibilidad(models.Model):
    DIA_CHOICES = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    cancha = models.ForeignKey(Cancha, on_delete=models.CASCADE, related_name='disponibilidades')
    dia_semana = models.IntegerField(choices=DIA_CHOICES)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    
    class Meta:
        unique_together = ('cancha', 'dia_semana', 'hora_inicio', 'hora_fin')

    def __str__(self):
        return f"{self.cancha.nombre} - {self.get_dia_semana_display()} ({self.hora_inicio} a {self.hora_fin})"
