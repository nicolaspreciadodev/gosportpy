Fase 1: Lógica de Cancelación (Prioridad Alta)
[x] Definir Estados: Agregar campo estado al modelo Reserva (Opciones: PROGRAMADA, COMPLETADA, CANCELADA).

[x] Validación de Tiempo: Crear lógica para que solo se pueda cancelar con X horas de anticipación (ej. 24h).

[x] Vista de Cancelación: Crear la función en views.py que cambie el estado y libere el horario de la cancha.

[x] Notificación: Implementar un mensaje de éxito (django.contrib.messages) tras cancelar.

[x] Tests de Cancelación: Escribir 2 tests (uno para cancelación exitosa y otro para intento de cancelación fuera de tiempo).

🔗 Fase 2: Integración de Navegación (Sidebar)
[x] Mapeo de URLs: Revisar base.html y reemplazar los # por los tags {% url 'nombre_vista' %} reales.

[x] Permisos en Menú: Usar {% if user.rol == 'DUEÑO' %} para mostrar/ocultar opciones de gestión de canchas.

[x] Active State: Resaltar el botón del sidebar según la página donde esté el usuario (clases de Tailwind condicionales).

🏆 Fase 3: Gestión de Torneos (Funcionalidad Nueva)
[x] Modelo Torneo: Crear tabla con nombre, fecha inicio, fecha fin y tipo de deporte.

[x] Relación con Canchas: Vincular torneos a una o varias canchas específicas.

[x] Inscripción: Lógica para que los equipos/usuarios puedan anotarse.

🎨 Fase 4: Pulido Estético (UI/UX)
[x] Auditoría de Tablas: Revisar si las tablas de reservas se ven bien en móvil (Responsive).

[x] Empty States: Mostrar un diseño bonito cuando el usuario no tenga reservas todavía ("Aún no tienes partidos, ¡reserva uno ahora!").