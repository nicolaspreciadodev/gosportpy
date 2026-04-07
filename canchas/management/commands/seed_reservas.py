from django.core.management.base import BaseCommand
import datetime
from django.utils import timezone
from canchas.models import Cancha, Disponibilidad
from negocio.models import Reserva, Factura
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Carga horarios logicos y reservas de prueba'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando carga de horarios (Disponibilidad) y Reservas...")

        canchas = Cancha.objects.all()
        depor1 = User.objects.get(username="depor_cop1")
        depor2 = User.objects.get(username="depor_cop2")

        # 1. Crear horarios lógicos
        for cancha in canchas:
            for i in range(5):
                Disponibilidad.objects.get_or_create(
                    cancha=cancha,
                    dia_semana=i,
                    defaults={'hora_inicio': datetime.time(18, 0), 'hora_fin': datetime.time(22, 0)}
                )
            for i in range(5, 7):
                Disponibilidad.objects.get_or_create(
                    cancha=cancha,
                    dia_semana=i,
                    defaults={'hora_inicio': datetime.time(8, 0), 'hora_fin': datetime.time(20, 0)}
                )
        self.stdout.write(self.style.SUCCESS("Disponibilidades creadas exitosamente."))

        # 2. Crear Reservas
        hoy = timezone.now().date()
        manana = hoy + datetime.timedelta(days=1)
        pasado_manana = hoy + datetime.timedelta(days=2)

        if canchas.exists():
            cacha = canchas.first()
            reserva1, c1 = Reserva.objects.get_or_create(
                usuario=depor1,
                cancha=cacha,
                fecha=manana,
                hora=datetime.time(19, 0),
                defaults={'estado': 'PROGRAMADA', 'pagado': False}
            )
            if c1:
                Factura.objects.get_or_create(reserva=reserva1, defaults={'total': cacha.precio})

        if canchas.count() > 1:
            cancha2 = canchas[1]
            reserva2, c2 = Reserva.objects.get_or_create(
                usuario=depor2,
                cancha=cancha2,
                fecha=pasado_manana,
                hora=datetime.time(20, 0),
                defaults={'estado': 'PROGRAMADA', 'pagado': True}
            )
            if c2:
                Factura.objects.get_or_create(reserva=reserva2, defaults={'total': cancha2.precio})

        self.stdout.write(self.style.SUCCESS("Mision cumplida."))
