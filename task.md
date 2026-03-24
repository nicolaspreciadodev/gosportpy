GoSport — Task Tracker
✅ Completado
Fase 0 — Setup inicial

Entorno virtual, dependencias, proyecto Django
Apps: core, usuarios, canchas, negocio
Configurar django-tailwind + theme

Fase 1 — Modelos y datos

CustomUser con roles DUEÑO / DEPORTISTA
Modelos: Cancha, Deporte, Disponibilidad
Modelos: Reserva, Factura, Torneo, Equipo
Seed data (canchas de prueba con imágenes)
requirements.txt generado

Fase 2 — Autenticación

Login con diseño profesional (CSS puro, Lucide, Inter/Montserrat)
Registro con selección de rol (card visual)
Reset de contraseña — 4 templates completos
auth.css centralizado (DRY)
16 tests en usuarios

Fase 3 — CRUD Canchas

Lista con filtro por deporte
Detalle de cancha
Crear / Editar / Eliminar (solo DUEÑO)
Validación de precio (> 0, < 1,000,000)
Verificación de propiedad (403 si otro dueño intenta editar)
9 tests en canchas

Fase 4 — Reservas y Facturas

Crear reserva (solo DEPORTISTA)
Validación anti-solapamiento
Señal: Factura se crea automáticamente
Vista de detalle de factura
Cancelación de reservas (validación 24h)
Estados: PROGRAMADA / COMPLETADA / CANCELADA

Fase 5 — Dashboard y Navegación

Dashboard diferenciado: DUEÑO / DEPORTISTA / ADMIN
Sidebar con active state y permisos por rol
Botón cancelar reserva en dashboard del deportista
Empty states en todas las secciones
Panel admin con stats + aprobación de torneos
Corrección bugs: user.role → user.rol, DUEÑO_CANCHA → DUEÑO

Fase 6 — Torneos y Equipos (Base)

Modelo Torneo con fecha_inicio, fecha_fin, deporte, canchas
Inscripción de equipos a torneos
Aprobación de torneos por superusuario
21 tests en negocio

Fase 7 — Disponibilidad real de canchas

Migrar modelo Disponibilidad a dia_semana (IntegerField 0-6)
Service: obtener_slots_disponibles()
Service: validar_slot_disponible()
Endpoint AJAX: DisponibilidadSlotsView
Vista: GestionarDisponibilidadView
Template: gestionar_disponibilidad.html
Template: crear_reserva.html con selector dinámico
Validación en CrearReservaView

Fase 8 — UX/UI & Testing

Sistema global de Toast Notifications en base.html
Limpieza de bloques {% if messages %} duplicados en templates
Revisión integral de flujos de usuario (UX audit)
Suite de tests corrida y validada
Seed data verificado con seed_db.py

✅ Completado
Fase 9 — Perfil de usuario

Vista: editar nombre, apellido, email
Vista: cambiar contraseña (logueado)
Template con estilo auth.css
Validar email único al editar (verificar cobertura de tests)
Tests: edición exitosa, email duplicado, contraseña incorrecta
26 tests en usuarios — todos PASS ✓

✅ Completado
Fase 10 — Sistema de Liga Completo ⭐ PRIORIDAD ALTA

Modelo: Partido (equipo_local, equipo_visitante, goles, estado, jornada, cancha, fecha) ✓
Modelo: PosicionEquipo (puntos, PJ, PG, PE, PP, GF, GC) con ordenamiento automático ✓
Extender Torneo: campo max_equipos, formato (LIGA / ELIMINACION), fixture_generado ✓
Migración de nuevos modelos ✓
Service: generar_fixture_liga() — algoritmo round-robin todos contra todos ✓
Service: registrar_resultado() — actualiza tabla de posiciones automáticamente ✓
Service: \_actualizar_posiciones() — helper privado DRY ✓
Vista: TorneoDetalleView — fixture + tabla de posiciones + equipos inscritos ✓
Vista: GenerarFixtureView — solo el organizador del torneo (RoleRequiredMixin) ✓
Vista: RegistrarResultadoView — organizador registra goles de cada partido ✓
Template: torneo_detalle.html — tabla de posiciones + calendario de partidos + modal ✓
Agregar rutas: torneos/<id>/, torneos/<id>/fixture/, partidos/<id>/resultado/ ✓
Validación: no inscribir equipos si ya se alcanzó max_equipos ✓
Tests: generación de fixture, registro de resultados, tabla de posiciones, edge cases ✓
Cobertura: 8 tests específicos de Liga + 21 tests negocio total — TODOS PASS ✓

✅ Completado
Fase 11 — Calificaciones de Canchas ⭐ PRIORIDAD ALTA

Modelo: Calificacion (usuario, cancha, puntuacion 1-5, comentario, fecha) ✓
Validación: solo usuarios que hayan completado una reserva en esa cancha ✓
Validación: una sola calificación por usuario por cancha (unique_together) ✓
Service: puede_calificar_cancha(usuario, cancha) ✓
Service: crear_calificacion(usuario, cancha, puntuacion, comentario) ✓
Service: obtener_calificaciones_cancha(cancha) ✓
Vista: CalificarCanchaView (POST-only) ✓
Vista: CanchaDetailView mejorada con calificaciones ✓
Template: cancha_detail.html con promedio, listado y formulario interactivo ✓
Estrellas interactivas con CSS (⭐ y ☆ Unicode) ✓
Tests: 7 tests de CalificarCanchaViewTest — TODOS PASS ✓
Database: Migration canchas.0004_calificacion aplicada ✓
Cobertura total canchas: 28 tests PASS (122.192s) ✓

⏳ Pendiente
Fase 12 — Emails Reales (SMTP) ⭐ PRIORIDAD ALTA

Configurar EMAIL_BACKEND con Gmail o SendGrid en settings.py
Agregar variables EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD al .env
Email: confirmación de reserva creada (con detalle de cancha, fecha y hora)
Email: recordatorio 24h antes de la reserva (Django management command o Celery)
Email: notificación al organizador cuando un equipo se inscribe a su torneo
Email: notificación al deportista cuando su torneo es aprobado
Template de email: HTML con estilo GoSport (logo + colores neon)
Tests: verificar que los emails se envían con el contenido correcto

Fase 13 — Pasarela de Pagos Real

Evaluar: Wompi vs MercadoPago (recomendado Wompi para Colombia)
Integrar SDK o API de la pasarela elegida
Vista: iniciar_pago() — genera enlace/widget de pago
Vista: webhook_pago() — recibe confirmación de pago de la pasarela
Actualizar Reserva.pagado = True desde el webhook
Manejo de pagos fallidos y reintentos
Template: página de pago con resumen de reserva
Tests: pago exitoso, pago fallido, webhook con firma inválida

Fase 14 — Búsqueda y Filtros Avanzados

Filtro por precio (rango min/max) en lista de canchas
Filtro por disponibilidad en fecha específica
Filtro por ciudad/zona (requiere agregar campo ciudad a Cancha)
Búsqueda por nombre de cancha (icontains)
Ordenamiento: por precio, por calificación, por más reservadas
UI: barra de filtros lateral o superior con reset filters
Tests: combinaciones de filtros, filtros vacíos, resultados vacíos

Fase 15 — Panel Analytics para el Dueño

Gráfica: reservas por mes (últimos 6 meses) por cancha
Gráfica: ingresos generados por cancha
Stat: horario más popular de cada cancha
Stat: tasa de cancelación
Stat: calificación promedio de sus canchas
Integrar Chart.js o similar en el dashboard del DUEÑO
Tests: cálculos de métricas con datos de prueba

Fase 16 — Perfil Público del Equipo

Vista pública: /equipos/<id>/ — nombre, logo, jugadores, historial de torneos
Tabla de estadísticas del equipo: PJ, PG, PE, PP, GF, GC, puntos totales históricos
Historial de partidos con resultados
Template: equipo_perfil.html con diseño consistente al resto de la app
Tests: acceso sin login, equipo inexistente (404)

Fase 17 — Foto de Perfil de Usuario

Agregar campo avatar (ImageField) a CustomUser
Migración del campo
Vista: subir/cambiar foto en perfil.html
Mostrar avatar en sidebar de base.html (reemplaza el círculo con inicial)
Resize automático de imagen al subir (usar Pillow)
Tests: subida válida, formato inválido, tamaño excesivo

Fase 18 — Producción

Instalar: python-decouple, gunicorn, psycopg2-binary, whitenoise (ya parcialmente hecho)
Crear .env con todas las variables
DEBUG=False, SECRET_KEY desde env, ALLOWED_HOSTS configurado
Migrar SQLite → PostgreSQL
Configurar archivos estáticos (collectstatic + whitenoise)
Configurar SMTP real
Setup Gunicorn como servidor WSGI
Deploy en Render / Railway / VPS
Documentar proceso de deploy en README.md

Fase 19 — Robustez (post-producción)

Aumentar test coverage a 70%+
Configurar logging centralizado (Django logging + archivo de log)
Backup automático de base de datos
CI/CD con GitHub Actions (tests en cada push al main)
Dockerizar aplicación (Dockerfile + docker-compose.yml)
Monitoring básico (UptimeRobot o Sentry para errores en producción)
