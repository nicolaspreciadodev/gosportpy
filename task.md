# GoSport — Task Tracker

## ✅ Completado

### Fase 0 — Setup inicial
- [x] Entorno virtual, dependencias, proyecto Django
- [x] Apps: core, usuarios, canchas, negocio
- [x] Configurar django-tailwind + theme

### Fase 1 — Modelos y datos
- [x] CustomUser con roles DUEÑO / DEPORTISTA
- [x] Modelos: Cancha, Deporte, Disponibilidad
- [x] Modelos: Reserva, Factura, Torneo, Equipo
- [x] Seed data (canchas de prueba con imágenes)
- [x] requirements.txt generado

### Fase 2 — Autenticación
- [x] Login con diseño profesional (CSS puro, Lucide, Inter/Montserrat)
- [x] Registro con selección de rol (card visual)
- [x] Reset de contraseña — 4 templates completos
- [x] auth.css centralizado (DRY)
- [x] 16 tests en usuarios

### Fase 3 — CRUD Canchas
- [x] Lista con filtro por deporte
- [x] Detalle de cancha
- [x] Crear / Editar / Eliminar (solo DUEÑO)
- [x] Validación de precio (> 0, < 1,000,000)
- [x] Verificación de propiedad (403 si otro dueño intenta editar)
- [x] 9 tests en canchas

### Fase 4 — Reservas y Facturas
- [x] Crear reserva (solo DEPORTISTA)
- [x] Validación anti-solapamiento
- [x] Señal: Factura se crea automáticamente
- [x] Vista de detalle de factura
- [x] Cancelación de reservas (validación 24h)
- [x] Estados: PROGRAMADA / COMPLETADA / CANCELADA

### Fase 5 — Dashboard y Navegación
- [x] Dashboard diferenciado: DUEÑO / DEPORTISTA / ADMIN
- [x] Sidebar con active state y permisos por rol
- [x] Botón cancelar reserva en dashboard del deportista
- [x] Empty states en todas las secciones
- [x] Panel admin con stats + aprobación de torneos
- [x] Corrección bugs: user.role → user.rol, DUEÑO_CANCHA → DUEÑO

### Fase 6 — Torneos y Equipos
- [x] Modelo Torneo con fecha_inicio, fecha_fin, deporte, canchas
- [x] Inscripción de equipos a torneos
- [x] Aprobación de torneos por superusuario
- [x] 21 tests en negocio

---

## 🔄 En progreso

### Fase 7 — Disponibilidad real de canchas
- [x] Migrar modelo Disponibilidad a dia_semana (IntegerField 0-6)
- [x] Service: obtener_slots_disponibles()
- [x] Service: validar_slot_disponible()
- [x] Endpoint AJAX: DisponibilidadSlotsView
- [x] Vista: GestionarDisponibilidadView
- [x] Template: gestionar_disponibilidad.html
- [x] Template: crear_reserva.html con selector dinámico
- [x] Validación en CrearReservaView
- [ ] Correr makemigrations + migrate
- [ ] Correr tests (objetivo: 48 tests en verde)
- [ ] Agregar botón "Horarios" en cancha_detail.html

---

## ⏳ Pendiente

### Fase 8 — Perfil de usuario
- [ ] Vista: editar nombre, apellido, email
- [ ] Vista: cambiar contraseña (logueado)
- [ ] Template con estilo auth.css
- [ ] Validar email único al editar
- [ ] Tests: edición exitosa, email duplicado, contraseña incorrecta

### Fase 9 — Panel de reservas del Dueño
- [ ] Vista: listar reservas de las canchas del dueño
- [ ] Filtros por fecha y estado
- [ ] El dueño puede cancelar reservas de sus canchas
- [ ] Template responsive (mobile-first)
- [ ] Tests de integración

### Fase 10 — Flujo de pagos
- [ ] Decidir: simular pago o pasarela real
- [ ] Si simulado: vista que marca pagado=True → redirige a factura
- [ ] Botón "Pagar Ahora" funcional en dashboard
- [ ] Factura se actualiza con fecha de pago
- [ ] Tests de integración

### Fase 11 — Producción
- [ ] Instalar: python-decouple, gunicorn, psycopg2-binary, whitenoise
- [ ] Crear .env con todas las variables
- [ ] Actualizar settings.py para leer .env
- [ ] DEBUG=False, SECRET_KEY desde env, ALLOWED_HOSTS configurado
- [ ] Migrar SQLite → PostgreSQL
- [ ] Configurar archivos estáticos (collectstatic + whitenoise)
- [ ] Configurar SMTP real (Gmail o SendGrid)
- [ ] Setup Gunicorn como servidor
- [ ] Deploy en Render / Railway / VPS
- [ ] Documentar proceso de deploy en README.md

### Fase 12 — Robustez (post-producción)
- [ ] Aumentar test coverage a 70%+
- [ ] Configurar logging centralizado
- [ ] Backup automático de base de datos
- [ ] CI/CD con GitHub Actions (tests en cada push)
- [ ] Dockerizar aplicación
- [ ] Monitoring básico

---

## 📊 Métricas actuales
- Tests: 39 ✅ (objetivo fase 7: 48)
- Coverage estimado: ~30%
- Features core: 85% completas
- Listo para producción: ❌ (faltan fases 11-12)