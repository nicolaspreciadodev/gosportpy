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
