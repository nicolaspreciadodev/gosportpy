from django.db import models
from django.conf import settings
from canchas.models import Cancha, Deporte

class Torneo(models.Model):
    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('PUBLICADO', 'Publicado'),
        ('RECHAZADO', 'Rechazado'),
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
    precio_inscripcion = models.DecimalField(max_digits=12, decimal_places=2, default=50000.00)
    
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
    hora = models.TimeField(help_text="Hora de inicio")
    hora_fin = models.TimeField(help_text="Hora de fin", null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PROGRAMADA')
    pagado = models.BooleanField(default=False)
    
    def clean(self):
        # Si no hay hora_fin, asumimos 1 hora
        import datetime
        dt_inicio = datetime.datetime.combine(self.fecha, self.hora)
        if not self.hora_fin:
            dt_fin = dt_inicio + datetime.timedelta(hours=1)
            self.hora_fin = dt_fin.time()
        else:
            dt_fin = datetime.datetime.combine(self.fecha, self.hora_fin)

        if dt_fin <= dt_inicio:
            raise ValidationError("La hora de fin debe ser posterior a la hora de inicio.")

        # Check overlap
        from django.db.models import Q
        overlapping = Reserva.objects.filter(
            cancha=self.cancha,
            fecha=self.fecha
        ).exclude(estado='CANCELADA')
        
        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)
            
        for res in overlapping:
            # Lógica de solapamiento de rangos
            res_inicio = datetime.datetime.combine(res.fecha, res.hora)
            res_fin = datetime.datetime.combine(res.fecha, res.hora_fin)
            
            if (dt_inicio < res_fin) and (dt_fin > res_inicio):
                raise ValidationError(f"La cancha {self.cancha.nombre} ya tiene una reserva en ese horario ({res.hora.strftime('%H:%M')} - {res.hora_fin.strftime('%H:%M')}).")

        # 4. Validar Fecha y Hora en el futuro
        from django.utils import timezone
        if dt_inicio < timezone.now():
            raise ValidationError("No puedes realizar una reserva en una fecha o hora que ya ha pasado.")

        # 5. Validar Disponibilidad de la Cancha (Horarios de apertura/cierre)
        dia_semana = self.fecha.weekday() # 0=Lunes, 6=Domingo
        from canchas.models import Disponibilidad
        dispos = Disponibilidad.objects.filter(cancha=self.cancha, dia_semana=dia_semana)
        
        if not dispos.exists():
            raise ValidationError(f"La cancha no está disponible los días {self.get_fecha_display_day()}.")
        
        # Debe estar contenido en al menos uno de los rangos de disponibilidad
        esta_dentro = False
        for disp in dispos:
            if self.hora >= disp.hora_inicio and self.hora_fin <= disp.hora_fin:
                esta_dentro = True
                break
        
        if not esta_dentro:
            horarios_str = " | ".join([f"{d.hora_inicio.strftime('%H:%M')} - {d.hora_fin.strftime('%H:%M')}" for d in dispos])
            raise ValidationError(f"Horario fuera de servicio. Disponibilidad para hoy: {horarios_str}")

    def get_fecha_display_day(self):
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        return dias[self.fecha.weekday()]

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

import uuid

class Factura(models.Model):
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='factura')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    referencia_pago = models.CharField(max_length=150, unique=True, null=True, blank=True)
    wompi_transaction_id = models.CharField(max_length=100, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.referencia_pago:
            # Generar referencia única tipo FACTURA-<uuid>
            self.referencia_pago = f"FACTURA-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)
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

class SolicitudModificacionTorneo(models.Model):
    """
    Representa una solicitud enviada por un dueño (organizador) al administrador
    para modificar un torneo que ya ha sido aprobado.
    """
    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
    )
    torneo = models.ForeignKey(Torneo, on_delete=models.CASCADE, related_name='solicitudes_modificacion')
    descripcion_cambio = models.TextField(help_text="Explique detalladamente qué cambios necesita hacer en el torneo.")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Solicitud para {self.torneo.nombre} ({self.get_estado_display()})"


class PromocionTorneo(models.Model):
    """
    Representa una solicitud de publicidad de un torneo en una cancha específica.
    """
    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
    )
    torneo = models.ForeignKey(Torneo, on_delete=models.CASCADE, related_name='promociones')
    cancha = models.ForeignKey(Cancha, on_delete=models.CASCADE, related_name='promociones')
    texto_promocional = models.TextField(help_text="Texto descriptivo para la publicidad del torneo.")
    imagen_promocional = models.ImageField(upload_to='promociones/', null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Publicidad {self.torneo.nombre} en {self.cancha.nombre} ({self.get_estado_display()})"

