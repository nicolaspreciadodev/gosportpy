from django.db import models
from django.conf import settings
from canchas.models import Cancha, Deporte

class Torneo(models.Model):
    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('PUBLICADO', 'Publicado'),
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    deporte = models.ForeignKey(Deporte, on_delete=models.CASCADE, null=True, blank=True)
    canchas = models.ManyToManyField(Cancha, related_name='torneos_list', blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    is_approved = models.BooleanField(default=False)
    organizador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='torneos_organizados')
    
    # Nuevos campos de Liga
    max_equipos = models.PositiveIntegerField(default=8)
    FORMATO_CHOICES = (
        ('LIGA', 'Liga (Todos contra todos)'),
        ('ELIMINACION', 'Eliminación Directa'),
    )
    formato = models.CharField(max_length=20, choices=FORMATO_CHOICES, default='LIGA')
    fixture_generado = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.nombre} ({self.get_estado_display()})"

from django.core.exceptions import ValidationError

class Reserva(models.Model):
    ESTADO_CHOICES = (
        ('PROGRAMADA', 'Programada'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    )
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservas')
    cancha = models.ForeignKey(Cancha, on_delete=models.CASCADE, related_name='reservas')
    fecha = models.DateField()
    hora = models.TimeField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PROGRAMADA')
    pagado = models.BooleanField(default=False)
    
    def clean(self):
        # Check if a reservation already exists for the same court, date, and hour
        overlapping = Reserva.objects.filter(
            cancha=self.cancha,
            fecha=self.fecha,
            hora=self.hora
        )
        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)
            
        if overlapping.exists():
            raise ValidationError(f"La cancha {self.cancha.nombre} ya se encuentra reservada para la fecha {self.fecha} a las {self.hora}.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def puede_cancelar(self):
        from django.utils import timezone
        import datetime
        # Combina fecha y hora de la reserva
        reserva_naive = datetime.datetime.combine(self.fecha, self.hora)
        # Asegurarse de que esté en formato de zona horaria si Django las usa
        try:
            reserva_dt = timezone.make_aware(reserva_naive)
        except ValueError: # Ya puede ser aware, aunque es raro en combine
            reserva_dt = reserva_naive
            
        time_difference = reserva_dt - timezone.now()
        return time_difference.total_seconds() >= 24 * 3600

    def __str__(self):
        return f"Reserva {self.id} - {self.cancha.nombre} ({self.fecha})"

class Factura(models.Model):
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='factura')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Factura {self.id} - {self.total}"

class Equipo(models.Model):
    nombre = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='equipos/', blank=True, null=True)
    jugadores = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='equipos')
    torneos = models.ManyToManyField(Torneo, related_name='equipos', blank=True)
    
    def __str__(self):
        return self.nombre

class Partido(models.Model):
    """
    Representa un partido dentro de un torneo (especialmente formato Liga).
    """
    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('JUGADO', 'Jugado'),
    )
    torneo = models.ForeignKey(Torneo, on_delete=models.CASCADE, related_name='partidos')
    equipo_local = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='partidos_local')
    equipo_visitante = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='partidos_visitante')
    goles_local = models.PositiveIntegerField(default=0)
    goles_visitante = models.PositiveIntegerField(default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    jornada = models.PositiveIntegerField()
    cancha = models.ForeignKey(Cancha, on_delete=models.SET_NULL, null=True, blank=True, related_name='partidos')
    fecha = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.equipo_local} vs {self.equipo_visitante} (Jornada {self.jornada})"

    class Meta:
        ordering = ['jornada', 'fecha']

class PosicionEquipo(models.Model):
    """
    Tabla de posiciones para un equipo en un torneo de formato Liga.
    """
    torneo = models.ForeignKey(Torneo, on_delete=models.CASCADE, related_name='posiciones')
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='posiciones_torneo')
    puntos = models.IntegerField(default=0)
    partidos_jugados = models.PositiveIntegerField(default=0)
    partidos_ganados = models.PositiveIntegerField(default=0)
    partidos_empatados = models.PositiveIntegerField(default=0)
    partidos_perdidos = models.PositiveIntegerField(default=0)
    goles_favor = models.PositiveIntegerField(default=0)
    goles_contra = models.PositiveIntegerField(default=0)
    
    @property
    def diferencia_goles(self):
        return self.goles_favor - self.goles_contra
        
    def __str__(self):
        return f"{self.equipo.nombre} - {self.puntos} pts ({self.torneo.nombre})"
        
    class Meta:
        ordering = ['-puntos', '-partidos_ganados', '-goles_favor']
        unique_together = ('torneo', 'equipo')
