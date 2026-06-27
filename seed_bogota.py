import os
import django
import random
from datetime import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GoSport.settings')
django.setup()

from usuarios.models import CustomUser
from canchas.models import Deporte, Cancha, Disponibilidad
from negocio.models import Torneo, Equipo, Reserva

def seed_bogota():
    print("Iniciando carga de datos reales de Bogotá...")

    # 1. Obtener o crear Deportes
    futbol, _ = Deporte.objects.get_or_create(nombre="Fútbol")
    tenis, _ = Deporte.objects.get_or_create(nombre="Tenis")
    basquet, _ = Deporte.objects.get_or_create(nombre="Básquet")

    deportes = [futbol, tenis, basquet]

    # 2. Crear 4 Dueños
    duenos = []
    for i in range(1, 5):
        username = f"dueno_bogota_{i}"
        user, created = CustomUser.objects.get_or_create(
            username=username,
            defaults={
                'email': f'dueno{i}@bogota.com',
                'rol': 'DUEÑO',
                'first_name': f'Propietario {i}',
                'last_name': 'Bogotá'
            }
        )
        if created:
            user.set_password('password123')
            user.save()
        duenos.append(user)

    # 3. Listado de Nombres y Direcciones Reales/Verosímiles en Bogotá
    canchas_data = [
        # Fútbol
        ("Canchas Maracaná Calle 80", "Calle 80 # 114-12", futbol),
        ("Canchas El Campincito", "Carrera 30 # 57-60", futbol),
        ("Gol Five Autonorte", "Autopista Norte # 193-20", futbol),
        ("Fair Play Bogotá", "Calle 170 # 58-02", futbol),
        ("Canchas Compensar Av 68", "Avenida 68 # 49-47", futbol),
        ("Soccer Future Suba", "Calle 145 # 92-30", futbol),
        ("Futbol Site 127", "Calle 127 # 7-15", futbol),
        ("Canchas La Jaula del Ángel", "Carrera 15 # 103-60", futbol),
        ("Babilonia Fútbol 5", "Calle 13 # 65-21", futbol),
        ("Xcoli Tenjo - Fútbol", "Vía Suba-Cota Km 4", futbol),

        # Tenis
        ("Bogotá Tennis Club Campestre", "Carrera 58 # 127-10", tenis),
        ("Club Los Lagartos (Tenis)", "Calle 116 # 72A-80", tenis),
        ("Tenis Parque Salitre", "Calle 63 # 68-45", tenis),
        ("Academia de Tenis Julio Varón", "Calle 153 # 50-20", tenis),
        ("Complejo de Tenis El Campín", "Carrera 24 # 53-50", tenis),
        ("Match Point Bogotá", "Calle 167 # 67-15", tenis),
        ("Canchas Polideportivo La Fragua", "Calle 15 Sur # 28-30", tenis),
        ("Tenis Club bogotá 134", "Calle 134 # 9-40", tenis),
        ("Rincón de Tenis", "Carrera 7 # 180-20", tenis),
        ("Tenis de la Sabana", "Autopista Norte Km 18", tenis),

        # Básquet
        ("Coliseo El Salitre (Auxiliar)", "Calle 63 # 68-45", basquet),
        ("Parque Alcázares Básquet", "Carrera 24 # 71-10", basquet),
        ("Canchas Movistar Arena", "Diagonal 61C # 26-36", basquet),
        ("Parque Nacional Enrique Olaya", "Carrera 7 # 36-00", basquet),
        ("Coliseo Cayetano Cañizares", "Carrera 80 # 40-55 Sur", basquet),
        ("Parque San Andrés", "Calle 82 # 100-30", basquet),
        ("Canchas Unicentro Bogotá", "Avenida 15 # 124-30", basquet),
        ("Parque Fontanar del Río", "Calle 144 # 141-00", basquet),
        ("Coliseo Parque Recreodeportivo El Salitre", "Carrera 60 # 63-65", basquet),
        ("Canchas Ciudad Salitre", "Calle 24 # 68-20", basquet),
    ]

    # 4. Crear las 30 Canchas
    print("Creando 30 canchas...")
    created_count = 0
    for nombre, direccion, deporte in canchas_data:
        # Asignar dueño de forma rotativa
        dueño = duenos[created_count % 4]
        
        cancha, created = Cancha.objects.get_or_create(
            nombre=nombre,
            defaults={
                'ubicacion': direccion,
                'deporte': deporte,
                'dueño': dueño,
                'precio': random.choice([80000, 100000, 120000, 150000, 180000]),
                'descripcion': f"Excelente cancha de {deporte.nombre} ubicada en {nombre}. Contamos con iluminación LED, vestuarios y zona social."
            }
        )

        # 5. Agregar Disponibilidad por defecto (rango completo)
        if created:
            for dia in range(7): # Todos los días
                Disponibilidad.objects.get_or_create(
                    cancha=cancha,
                    dia_semana=dia,
                    hora_inicio=time(8, 0),
                    hora_fin=time(22, 0)
                )
            created_count += 1

    print(f"¡Éxito! Se crearon {created_count} canchas en Bogotá.")

if __name__ == "__main__":
    seed_bogota()
