# Guía de Despliegue - GoSport

Esta guía detalla el proceso para desplegar el proyecto GoSport en un servidor o servicio en la nube como Render, Railway o un VPS tradicional (DigitalOcean, AWS, etc.).

## 1. Requisitos Previos

- Python 3.12+ o superior.
- PostgreSQL en producción.
- Gunicorn (ya configurado en `requirements.txt`).
- `whitenoise` para servir archivos estáticos (configurado en `settings.py`).
- `python-decouple` para la gestión segura de variables de entorno.
- `dj-database-url` para unificar la conexión string de DB.

## 2. Variables de Entorno (.env)

Debes crear un archivo o inyectar las siguientes variables de entorno en el servidor de despliegue:

```env
# Ejemplo
DEBUG=False
SECRET_KEY=clave_aleatoria_muy_segura_aqui_generada_1234
ALLOWED_HOSTS=.tudominio.com,gosport-prod.up.railway.app

# Tu cadena de conexión generada por tu cluster de Postgres
DATABASE_URL=postgres://usuario:contraseña@servidor.com:5432/nombre_db
```

## 3. Comandos de Inicio y Configuración (VPS)

1. **Clonar proyecto e instalar dependencias:**
   ```bash
   git clone [url_repo]
   cd gosportpy
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Migrar base de datos Postgres:**
   ```bash
   python manage.py migrate
   ```

3. **Recolectar estáticos:**
   Con la integración de WhiteNoise, debemos agrupar los estáticos:
   ```bash
   python manage.py collectstatic --noinput
   ```

4. **Crear superusuario:**
   ```bash
   python manage.py createsuperuser
   ```

## 4. Ejecutar con Gunicorn

El proyecto ahora utiliza Gunicorn en lugar del servidor de desarrollo nativo de Django, el cual no está optimizado para producción.

Comando de inicio:
```bash
gunicorn GoSport.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

*(El número de workers generalmente se recomienda como `2 * NUM_CORES + 1`).*

## 5. Plataformas PaaS (Railway / Render / Heroku)

Si usas Railway o Render, lo único que tienes que hacer es:
1. Conectar tu repositorio de GitHub.
2. Definir el `Start Command`: `gunicorn GoSport.wsgi:application`
3. Incluir Postgres en la infraestructura del clúster de Railway/Render.
4. Agregar las Env Vars exactas desde su interfaz web (usando la cadena de conexión generada por el servicio Postgres que ellos proveen para el `DATABASE_URL`).
5. Ellos ejecutarán `collectstatic` automáticamente si detectan Django en el build.
