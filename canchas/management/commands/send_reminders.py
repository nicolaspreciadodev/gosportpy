from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from negocio.models import Reserva
from core.emails import enviar_recordatorio_reserva

class Command(BaseCommand):
    help = 'Envía correos electrónicos de recordatorio a los usuarios con reservas programadas para mañana.'

    def handle(self, *args, **kwargs):
        manana = timezone.localdate() + timedelta(days=1)
        
        reservas_manana = Reserva.objects.filter(
            fecha=manana,
            estado='PROGRAMADA'
        )

        count = reservas_manana.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS(f'No hay reservas programadas para mañana ({manana}).'))
            return

        self.stdout.write(f'Encontradas {count} reservas para mañana. Enviando recordatorios...')

        exitosos = 0
        fallidos = 0

        for reserva in reservas_manana:
            try:
                enviar_recordatorio_reserva(reserva)
                exitosos += 1
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Error enviando recordatorio para reserva {reserva.id}: {e}'))
                fallidos += 1

        self.stdout.write(self.style.SUCCESS(
            f'Finalizado. Recordatorios exitosos: {exitosos}, Fallidos: {fallidos}'
        ))
