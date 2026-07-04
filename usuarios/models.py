from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('DUEÑO', 'Court Owner'),
        ('DEPORTISTA', 'Athlete'),
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
        ('PENDIENTE', 'Pending'),
        ('APROBADO', 'Approved'),
        ('RECHAZADO', 'Rejected'),
    )
    usuario = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='solicitudes_rol',
        verbose_name='Requesting User',
    )
    motivo = models.TextField(
        help_text='Explain why you want to register your court on GoSport.',
        verbose_name='Request Reason',
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='PENDIENTE',
        verbose_name='Status',
    )
    fecha_solicitud = models.DateTimeField(auto_now_add=True, verbose_name='Request Date')
    fecha_respuesta = models.DateTimeField(null=True, blank=True, verbose_name='Response Date')
    notas_admin = models.TextField(
        blank=True,
        verbose_name='Admin Notes',
        help_text='Reason for approval or rejection (visible to the user).',
    )

    class Meta:
        verbose_name = 'Role Request'
        verbose_name_plural = 'Role Requests'
        ordering = ['-fecha_solicitud']

    def __str__(self):
        return f"Solicitud de {self.usuario.username} — {self.get_estado_display()}"
