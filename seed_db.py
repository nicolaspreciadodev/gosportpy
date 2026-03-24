import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GoSport.settings')
django.setup()

from usuarios.models import CustomUser
from canchas.models import Deporte, Cancha, Calificacion
from negocio.models import Torneo, Equipo, Reserva

print("Poblando base de datos con datos de prueba...")

# 1. Eliminar datos existentes para empezar limpio
CustomUser.objects.all().delete()
Deporte.objects.all().delete()

# 2. Crear Deportes
futbol = Deporte.objects.create(nombre="Fútbol")
tenis = Deporte.objects.create(nombre="Tenis")
basquet = Deporte.objects.create(nombre="Básquet")

# 3. Crear Usuarios
print("Creando usuarios...")
admin = CustomUser.objects.create_superuser('admin', 'admin@gosport.com', 'admin123', rol='DUEÑO')

dueno = CustomUser.objects.create_user(
    username='dueno',
    email='dueno@gosport.com',
    password='password123',
    rol='DUEÑO',
    first_name='Carlos',
    last_name='Gestor'
)

deportista1 = CustomUser.objects.create_user(
    username='deportista1',
    email='dep1@gosport.com',
    password='password123',
    rol='DEPORTISTA',
    first_name='Juan',
    last_name='Pérez'
)

deportista2 = CustomUser.objects.create_user(
    username='deportista2',
    email='dep2@gosport.com',
    password='password123',
    rol='DEPORTISTA',
    first_name='María',
    last_name='Gómez'
)

# 4. Crear Cancha para el DUEÑO
print("Creando canchas y equipos...")
cancha_futbol = Cancha.objects.create(
    nombre="Cancha El Maracaná",
    precio=150.00,
    ubicacion="Av. Principal 123",
    dueño=dueno,
    deporte=futbol
)

# 5. Crear Equipo y Torneos
equipo = Equipo.objects.create(nombre="Los Relámpagos")
equipo.jugadores.add(deportista1, deportista2)

from datetime import date, timedelta
from django.utils import timezone
futuro = timezone.now().date() + timedelta(days=10)

torneo_publicado = Torneo.objects.create(
    nombre="Copa de Verano 2026",
    descripcion="El mejor torneo de Fútbol amateur.",
    fecha_inicio=futuro,
    fecha_fin=futuro + timedelta(days=5),
    deporte=futbol,
    organizador=dueno,
    estado="PUBLICADO",
    is_approved=True
)
torneo_publicado.canchas.add(cancha_futbol)

# 6. Crear Reservas PASADAS para poder calificar
print("Creando reservas pasadas...")
from datetime import datetime, time

pasado = timezone.now().date() - timedelta(days=2)
reserva_completada = Reserva.objects.create(
    usuario=deportista1,
    cancha=cancha_futbol,
    fecha=pasado,
    hora=time(14, 30),
    estado='COMPLETADA',
    pagado=True
)

# 7. Crear Calificaciones de ejemplo
print("Creando calificaciones de ejemplo...")
Calificacion.objects.create(
    usuario=deportista1,
    cancha=cancha_futbol,
    puntuacion=5,
    comentario="¡Excelente cancha! Muy bien mantenida y las canchas de calidad premium. ⭐"
)

Calificacion.objects.create(
    usuario=deportista2,
    cancha=cancha_futbol,
    puntuacion=4,
    comentario="Buenos espacios, pero el césped necesita un poco más de mantenimiento."
)

print("¡Datos de prueba generados exitosamente!")
