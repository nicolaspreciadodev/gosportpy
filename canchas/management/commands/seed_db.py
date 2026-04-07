import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from canchas.models import Deporte, Cancha, Disponibilidad
from negocio.models import Torneo, Equipo

User = get_user_model()

class Command(BaseCommand):
    help = 'Pobla la base de datos con datos simulados iniciales (COP).'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando carga de datos Seed...")

        # 1. Crear Deportes
        deportes = ["Fútbol 5", "Fútbol 11", "Tenis", "Baloncesto", "Pádel"]
        deporte_objs = {}
        for d in deportes:
            obj, created = Deporte.objects.get_or_create(nombre=d)
            deporte_objs[d] = obj
            if created:
                self.stdout.write(f"- Creado Deporte: {d}")

        # 2. Crear Usuarios (Roles: DUEÑO, DEPORTISTA, ADMIN)
        dueño1, _ = User.objects.get_or_create(username="dueño_cop", defaults={
            "email": "dueño@gosport.com.co", "rol": "DUEÑO"
        })
        if _: dueño1.set_password("admin123"); dueño1.save()

        deportista1, _ = User.objects.get_or_create(username="depor_cop1", defaults={
            "email": "jugador1@gosport.com.co", "rol": "DEPORTISTA"
        })
        if _: deportista1.set_password("admin123"); deportista1.save()

        deportista2, _ = User.objects.get_or_create(username="depor_cop2", defaults={
            "email": "jugador2@gosport.com.co", "rol": "DEPORTISTA"
        })
        if _: deportista2.set_password("admin123"); deportista2.save()

        admin, _ = User.objects.get_or_create(username="admin_cop", defaults={
            "email": "admin@gosport.com.co", "rol": "ADMIN", "is_staff": True, "is_superuser": True
        })
        if _: admin.set_password("admin123"); admin.save()

        # 3. Crear Canchas (En pesos colombianos COP)
        cancha_data = [
            {"nombre": "Sintética El Campín (F5)", "deporte": deporte_objs["Fútbol 5"], "precio": 80000.00, "ciudad": "Bogotá", "ubicacion": "Bosa Centro"},
            {"nombre": "Cancha Coliseo Salitre (BKT)", "deporte": deporte_objs["Baloncesto"], "precio": 60000.00, "ciudad": "Bogotá", "ubicacion": "Bosa Laureles"},
            {"nombre": "Club Pádel Norte", "deporte": deporte_objs["Pádel"], "precio": 120000.00, "ciudad": "Bogotá", "ubicacion": "Bosa Piamonte"}
        ]
        
        cancha_objs = []
        for c_data in cancha_data:
            cancha, created = Cancha.objects.get_or_create(
                nombre=c_data["nombre"],
                defaults={
                    "deporte": c_data["deporte"],
                    "precio": c_data["precio"],
                    "ciudad": c_data["ciudad"],
                    "ubicacion": c_data["ubicacion"],
                    "dueño": dueño1
                }
            )
            cancha_objs.append(cancha)
            if created:
                self.stdout.write(f"- Creada Cancha: {cancha.nombre} (${cancha.precio} COP)")

        # 4. Crear Torneo 
        proximo_mes = timezone.now().date() + datetime.timedelta(days=15)
        torneo, created = Torneo.objects.get_or_create(
            nombre="Copa Relámpago Bogotá 2026",
            defaults={
                "organizador": dueño1,
                "deporte": deporte_objs["Fútbol 5"],
                "max_equipos": 8,
                "precio_inscripcion": 150000.00,
                "estado": "PUBLICADO",
                "is_approved": True,
                "fecha_inicio": proximo_mes,
                "formato": "LIGA"
            }
        )
        if created:
            self.stdout.write(f"- Creado Torneo: {torneo.nombre} a ${torneo.precio_inscripcion} COP")

        # Asignar canchas al torneo
        if not torneo.canchas.exists():
            torneo.canchas.add(cancha_objs[0])

        # 5. Crear Equipos e inscribir 1 equipo en Torneo
        equipo, e_created = Equipo.objects.get_or_create(nombre="Los Galácticos FC")
        if e_created:
            equipo.jugadores.add(deportista1)
            equipo.jugadores.add(deportista2)
            equipo.torneos.add(torneo)
            self.stdout.write(f"- Creado Equipo: {equipo.nombre} (Suscrito a Torneo)")

        self.stdout.write(self.style.SUCCESS("¡Semilla ejecutada correctamente con éxito (Datos en COP)!"))
