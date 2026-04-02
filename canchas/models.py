from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Deporte(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre

class Cancha(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    ubicacion = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=100, default='Bogotá')
    imagen = models.ImageField(upload_to='canchas/', blank=True, null=True)
    dueño = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='canchas')
    deporte = models.ForeignKey(Deporte, on_delete=models.SET_NULL, null=True, related_name='canchas')

    def __str__(self):
        return self.nombre

    @property
    def promedio_calificacion(self):
        """Retorna el promedio de calificaciones (1-5) o None si no hay."""
        calificaciones = self.calificaciones.all()
        if not calificaciones.exists():
            return None
        total = sum(c.puntuacion for c in calificaciones)
        return round(total / calificaciones.count(), 1)

    @property
    def total_calificaciones(self):
        """Retorna cantidad de calificaciones."""
        return self.calificaciones.count()

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


class Calificacion(models.Model):
    """Modelo para las calificaciones/reviews de canchas.

    Restricciones:
    - Solo se puede calificar si se tiene una Reserva completada en esa cancha
    - Una sola calificación por usuario por cancha (unique_together)
    - Puntuación: 1-5 estrellas
    - Comentario opcional
    """

    cancha = models.ForeignKey(Cancha, on_delete=models.CASCADE, related_name='calificaciones')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='calificaciones')
    puntuacion = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Puntuación de 1 a 5 estrellas'
    )
    comentario = models.TextField(blank=True, max_length=500)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cancha', 'usuario')
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.usuario.username} - {self.cancha.nombre} ({self.puntuacion}★)"
