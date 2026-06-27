from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from negocio.models import Reserva, Factura

@receiver(post_save, sender=Reserva)
def crear_factura_reserva(sender, instance, created, **kwargs):
    if created:
        import datetime
        inicio = datetime.datetime.combine(instance.fecha, instance.hora)
        fin = datetime.datetime.combine(instance.fecha, instance.hora_fin)
        duracion = fin - inicio
        horas = duracion.total_seconds() / 3600.0
        
        Factura.objects.create(
            reserva=instance,
            total=instance.cancha.precio * Decimal(horas)
        )
