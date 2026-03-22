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
