from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('DUEÑO', 'Dueño de Cancha'),
        ('DEPORTISTA', 'Deportista'),
    )
    rol = models.CharField(max_length=20, choices=ROLE_CHOICES, default='DEPORTISTA')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"


class SolicitudRolDueño(models.Model):
    """Solicitud de un Deportista para convertirse en Dueño de Cancha.

    El flujo es:
        1. El Deportista crea una solicitud con un motivo.
        2. El SuperAdmin la revisa y la Aprueba o Rechaza.
        3. Si se aprueba, el rol del usuario cambia a 'DUEÑO' automáticamente.
    """
    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
    )
    usuario = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='solicitudes_rol',
        verbose_name='Usuario solicitante',
    )
    motivo = models.TextField(
        help_text='Explica por qué deseas registrar tu cancha en GoSport.',
        verbose_name='Motivo de la solicitud',
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='PENDIENTE',
        verbose_name='Estado',
    )
    fecha_solicitud = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de solicitud')
    fecha_respuesta = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de respuesta')
    notas_admin = models.TextField(
        blank=True,
        verbose_name='Notas del administrador',
        help_text='Motivo de aprobación o rechazo (visible para el usuario).',
    )

    class Meta:
        verbose_name = 'Solicitud de Rol Dueño'
        verbose_name_plural = 'Solicitudes de Rol Dueño'
        ordering = ['-fecha_solicitud']

    def __str__(self):
        return f"Solicitud de {self.usuario.username} — {self.get_estado_display()}"
