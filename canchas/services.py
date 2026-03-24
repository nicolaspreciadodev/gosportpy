from django.core.exceptions import PermissionDenied
from .models import Cancha, Deporte


def obtener_canchas_del_dueño(usuario):
    """Retorna todas las canchas que pertenecen al dueño dado.

    Args:
        usuario: Instancia de CustomUser con rol DUEÑO.

    Returns:
        QuerySet de Cancha filtrado por dueño.
    """
    return Cancha.objects.filter(dueño=usuario).select_related('deporte')


def crear_cancha(datos_form, dueño):
    """Crea y persiste una nueva Cancha asignándole el dueño automáticamente.

    Args:
        datos_form: Form validado (form.save(commit=False) ya aplicado).
        dueño: Usuario con rol DUEÑO que será el propietario.

    Returns:
        Instancia de Cancha recién creada.
    """
    datos_form.dueño = dueño
    datos_form.save()
    return datos_form


def verificar_propiedad(cancha, usuario):
    """Lanza PermissionDenied si el usuario no es el dueño de la cancha.

    Args:
        cancha: Instancia de Cancha a verificar.
        usuario: Usuario autenticado que intenta operar.

    Raises:
        PermissionDenied: Si el usuario no es el propietario.
    """
    if cancha.dueño != usuario:
        raise PermissionDenied("No tienes permiso para modificar esta cancha.")


import datetime
from django.apps import apps

def _generar_slots_por_hora(hora_inicio, hora_fin):
    """Genera slots de 1 hora entre hora_inicio y hora_fin."""
    slots = []
    actual = datetime.datetime.combine(datetime.date.today(), hora_inicio)
    fin = datetime.datetime.combine(datetime.date.today(), hora_fin)
    while actual < fin:
        slots.append(actual.time())
        actual += datetime.timedelta(hours=1)
    return slots

def obtener_slots_disponibles(cancha_id, fecha):
    """
    Retorna una lista de time objects con los slots disponibles
    para una cancha en una fecha específica (1 hora cada slot).
    """
    if isinstance(fecha, str):
        fecha = datetime.datetime.strptime(fecha, '%Y-%m-%d').date()

    dia_semana = fecha.weekday() # 0-6 (Lunes a Domingo)

    disponibilidades = Cancha.objects.get(id=cancha_id).disponibilidades.filter(dia_semana=dia_semana)

    Reserva = apps.get_model('negocio', 'Reserva')
    reservas_dia = Reserva.objects.filter(
        cancha_id=cancha_id, fecha=fecha
    ).exclude(estado='CANCELADA').values_list('hora', flat=True)

    slots_disponibles = []
    reservas_set = set(reservas_dia)

    for disp in disponibilidades:
        slots = _generar_slots_por_hora(disp.hora_inicio, disp.hora_fin)
        for slot in slots:
            if slot not in reservas_set and slot not in slots_disponibles:
                slots_disponibles.append(slot)

    return sorted(slots_disponibles)

def validar_slot_disponible(cancha_id, fecha, hora):
    """
    Verifica si una hora específica está disponible para una reserva.
    """
    slots = obtener_slots_disponibles(cancha_id, fecha)
    if isinstance(hora, str):
        # Asegurar formato time
        try:
            hora = datetime.datetime.strptime(hora, '%H:%M:%S').time()
        except ValueError:
            hora = datetime.datetime.strptime(hora, '%H:%M').time()

    return hora in slots


# ===== FASE 11: CALIFICACIONES =====

def puede_calificar_cancha(usuario, cancha):
    """Verifica si un usuario puede calificar una cancha.

    Solo puede calificar si tiene al menos una Reserva completada
    en esa cancha.

    Args:
        usuario: CustomUser autenticado
        cancha: Instancia de Cancha

    Returns:
        bool: True si puede calificar, False en caso contrario
    """
    Reserva = apps.get_model('negocio', 'Reserva')
    return Reserva.objects.filter(
        usuario=usuario,
        cancha=cancha,
        estado='COMPLETADA'
    ).exists()


def crear_calificacion(usuario, cancha, puntuacion, comentario=''):
    """Crea una calificación para una cancha.

    Validaciones:
    - Usuario debe tener al menos una Reserva completada
    - No puede haber calificación previa del usuario para la cancha
    - Puntuación debe estar entre 1-5

    Args:
        usuario: CustomUser autenticado
        cancha: Instancia de Cancha
        puntuacion: int (1-5)
        comentario: str opcional (máx 500 caracteres)

    Returns:
        Calificacion: Instancia recién creada

    Raises:
        PermissionDenied: Si no tiene reserva completada
        ValidationError: Si ya existe calificación o puntuación inválida
    """
    from django.core.exceptions import ValidationError
    from .models import Calificacion

    # Verificar que puede calificar
    if not puede_calificar_cancha(usuario, cancha):
        raise PermissionDenied(
            'Solo puedes calificar si completaste una reserva en esta cancha.'
        )

    # Verificar que no exista calificación previa
    if Calificacion.objects.filter(usuario=usuario, cancha=cancha).exists():
        raise ValidationError(
            'Ya habías calificado esta cancha. Cada usuario solo puede calificar una vez.'
        )

    # Validar puntuación
    if not (1 <= puntuacion <= 5):
        raise ValidationError('La puntuación debe estar entre 1 y 5.')

    # Crear calificación
    calificacion = Calificacion.objects.create(
        usuario=usuario,
        cancha=cancha,
        puntuacion=puntuacion,
        comentario=comentario.strip()
    )

    return calificacion


def obtener_calificaciones_cancha(cancha):
    """Retorna todas las calificaciones de una cancha ordenadas por fecha.

    Args:
        cancha: Instancia de Cancha

    Returns:
        QuerySet de Calificacion ordenadas por fecha descendente
    """
    from .models import Calificacion
    return Calificacion.objects.filter(cancha=cancha).select_related('usuario')
