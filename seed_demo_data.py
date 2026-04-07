import datetime
from django.utils import timezone
from canchas.models import Cancha, Disponibilidad
from negocio.models import Reserva, Factura
from django.contrib.auth import get_user_model

User = get_user_model()

def run():
    print("Iniciando carga de horarios (Disponibilidad) y Reservas...")

    canchas = Cancha.objects.all()
    depor1 = User.objects.get(username="depor_cop1")
    depor2 = User.objects.get(username="depor_cop2")

    # 1. Crear horarios lógicos (18:00 a 22:00 para Lunes a Viernes, 08:00 a 20:00 para Sábados y Domingos)
    print("Creando disponibilidades...")
    for cancha in canchas:
        # Lunes a Viernes (0 a 4)
        for i in range(5):
            Disponibilidad.objects.get_or_create(
                cancha=cancha,
                dia_semana=i,
                defaults={'hora_inicio': datetime.time(18, 0), 'hora_fin': datetime.time(22, 0)}
            )
        # Sábado y Domingo (5 y 6)
        for i in range(5, 7):
            Disponibilidad.objects.get_or_create(
                cancha=cancha,
                dia_semana=i,
                defaults={'hora_inicio': datetime.time(8, 0), 'hora_fin': datetime.time(20, 0)}
            )
    print("Disponibilidades creadas exitosamente.")

    # 2. Crear Reservas Activas para los próximos días
    print("Generando Reservas...")
    
    # Calcular fechas para reservas (mañana y pasado mañana)
    hoy = timezone.now().date()
    manana = hoy + datetime.timedelta(days=1)
    pasado_manana = hoy + datetime.timedelta(days=2)

    # Reservas de Deportista 1
    if canchas.exists():
        cancha_1 = canchas.first()
        reserva1, c1 = Reserva.objects.get_or_create(
            usuario=depor1,
            cancha=cancha_1,
            fecha=manana,
            hora=datetime.time(19, 0),
            defaults={'estado': 'PROGRAMADA', 'pagado': False}
        )
        if c1:
            Factura.objects.get_or_create(reserva=reserva1, defaults={'total': cancha_1.precio})
            print(f"Reserva creada para {depor1.username} en {cancha_1.nombre}")

    # Reservas de Deportista 2
    if canchas.count() > 1:
        cancha_2 = canchas[1]
        reserva2, c2 = Reserva.objects.get_or_create(
            usuario=depor2,
            cancha=cancha_2,
            fecha=pasado_manana,
            hora=datetime.time(20, 0),
            defaults={'estado': 'PROGRAMADA', 'pagado': True}  # Pagado!
        )
        if c2:
            Factura.objects.get_or_create(reserva=reserva2, defaults={'total': cancha_2.precio})
            print(f"Reserva creada para {depor2.username} en {cancha_2.nombre}")

    print("Proceso finalizado. Horarios y reservas inyectados con éxito.")

if __name__ == '__main__':
    run()
