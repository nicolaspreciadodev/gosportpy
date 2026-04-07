import os
import django
from urllib.request import urlopen
from django.core.files.base import ContentFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GoSport.settings')
django.setup()

from canchas.models import Cancha

images = {
    "Fútbol 5": "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?w=800&q=80",
    "Baloncesto": "https://images.unsplash.com/photo-1505666287802-931dc83948e9?w=800&q=80",
    "Pádel": "https://images.unsplash.com/photo-1595435934249-5df7ed86e1c0?w=800&q=80"
}

canchas = Cancha.objects.all()

for cancha in canchas:
    if cancha.deporte and cancha.deporte.nombre in images:
        print(f"Descargando imagen para {cancha.nombre} ({cancha.deporte.nombre})...")
        try:
            response = urlopen(images[cancha.deporte.nombre])
            image_content = response.read()
            filename = f"default_{cancha.deporte.nombre.replace(' ', '_').lower()}.jpg"
            cancha.imagen.save(filename, ContentFile(image_content), save=True)
            print(f"Imagen adjuntada a {cancha.nombre}.")
        except Exception as e:
            print(f"Error descargando imagen para {cancha.nombre}: {e}")
    else:
        print(f"No hay imagen predeterminada para el deporte de {cancha.nombre}.")

print("Proceso finalizado.")
