"""
Vistas CRUD para la gestión de canchas deportivas.

Estructura:
    - CanchaListView     → GET  /canchas/
    - CanchaDetailView   → GET  /canchas/<pk>/
    - CanchaCreateView   → GET/POST /canchas/nueva/
    - CanchaUpdateView   → GET/POST /canchas/<pk>/editar/
    - CanchaDeleteView   → GET/POST /canchas/<pk>/eliminar/
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from core.mixins import RoleRequiredMixin
from .models import Cancha, Deporte
from .forms import CanchaForm
from django.db.models import Avg, Count
import datetime
from . import services

class CanchaListView(View):
    """Lista pública de todas las canchas disponibles.

    Soporta filtrado por deporte vía query param ?deporte=<id>.
    Accesible para cualquier usuario autenticado.
    """

    def get(self, request):
        canchas = Cancha.objects.select_related('deporte', 'dueño').all()
        
        deporte_id = request.GET.get('deporte')
        q = request.GET.get('q')
        min_precio = request.GET.get('min_precio')
        max_precio = request.GET.get('max_precio')
        ciudad = request.GET.get('ciudad')
        fecha = request.GET.get('fecha')
        orden = request.GET.get('orden')

        if deporte_id:
            canchas = canchas.filter(deporte__id=deporte_id)
        if q:
            canchas = canchas.filter(nombre__icontains=q)
        if ciudad:
            canchas = canchas.filter(ciudad__icontains=ciudad)
        if min_precio:
            try: canchas = canchas.filter(precio__gte=float(min_precio))
            except ValueError: pass
        if max_precio:
            try: canchas = canchas.filter(precio__lte=float(max_precio))
            except ValueError: pass
            
        if fecha:
            try:
                # Validar disponibilidad por día de la semana
                fecha_obj = datetime.datetime.strptime(fecha, "%Y-%m-%d").date()
                dia_semana_num = fecha_obj.weekday()  # Lunes 0, Domingo 6
                # Solo canchas que tienen disponibilidad ese día
                canchas = canchas.filter(disponibilidades__dia_semana=dia_semana_num).distinct()
            except ValueError:
                pass
                
        # Ordenamiento dinámico
        if orden == 'precio_asc':
            canchas = canchas.order_by('precio')
        elif orden == 'precio_desc':
            canchas = canchas.order_by('-precio')
        elif orden == 'mejor_calificadas':
            # Usa el related_name calificaciones del modelo
            canchas = canchas.annotate(promedio=Avg('calificaciones__puntuacion')).order_by('-promedio')
        elif orden == 'mas_reservadas':
            # Usa el related_name reservas de Cancha (definido en negocio.Reserva)
            canchas = canchas.annotate(num_reservas=Count('reservas')).order_by('-num_reservas')

        ciudades_disponibles = Cancha.objects.values_list('ciudad', flat=True).distinct()

        context = {
            'canchas': canchas,
            'deportes': Deporte.objects.all(),
            'deporte_activo': deporte_id,
            'q': q,
            'min_precio': min_precio,
            'max_precio': max_precio,
            'ciudad_activa': ciudad,
            'fecha_activa': fecha,
            'orden_activo': orden,
            'ciudades': ciudades_disponibles,
        }
        return render(request, 'canchas/cancha_list.html', context)


class CanchaDetailView(View):
    """Detalle de una cancha con disponibilidad, botón de reserva y calificaciones.

    Context:
        cancha: instancia de Cancha con detalles completos
        calificaciones: lista de Calificacion ordenadas por fecha descendente
        puede_calificar: bool indicando si el usuario autenticado puede calificar
    """

    def get(self, request, pk):
        cancha = get_object_or_404(
            Cancha.objects.select_related('deporte', 'dueño'), pk=pk
        )
        calificaciones = services.obtener_calificaciones_cancha(cancha)
        puede_calificar = False

        if request.user.is_authenticated and request.user.rol == 'DEPORTISTA':
            puede_calificar = services.puede_calificar_cancha(request.user, cancha)

        context = {
            'cancha': cancha,
            'calificaciones': calificaciones,
            'puede_calificar': puede_calificar,
        }
        return render(request, 'canchas/cancha_detail.html', context)


class CanchaCreateView(RoleRequiredMixin, View):
    """Permite a un DUEÑO crear una nueva cancha.

    El campo `dueño` se asigna automáticamente desde el usuario en sesión
    a través del service layer (principio DRY).
    """
    allowed_roles = ['DUEÑO']

    def get(self, request):
        return render(request, 'canchas/cancha_form.html', {'form': CanchaForm()})

    def post(self, request):
        form = CanchaForm(request.POST, request.FILES)
        if form.is_valid():
            cancha = form.save(commit=False)
            crear_cancha_instance = services.crear_cancha(cancha, request.user)
            messages.success(request, f'¡Cancha "{crear_cancha_instance.nombre}" creada exitosamente!')
            return redirect('canchas:detalle', pk=crear_cancha_instance.pk)

        return render(request, 'canchas/cancha_form.html', {'form': form})


class CanchaUpdateView(RoleRequiredMixin, View):
    """Permite a un DUEÑO editar su propia cancha.

    Verifica propiedad antes de mostrar o procesar el formulario.
    """
    allowed_roles = ['DUEÑO']

    def _get_cancha_propia(self, pk, usuario):
        """Helper: obtiene la cancha y valida propiedad."""
        cancha = get_object_or_404(Cancha, pk=pk)
        services.verificar_propiedad(cancha, usuario)
        return cancha

    def get(self, request, pk):
        cancha = self._get_cancha_propia(pk, request.user)
        form = CanchaForm(instance=cancha)
        return render(request, 'canchas/cancha_form.html', {'form': form, 'cancha': cancha})

    def post(self, request, pk):
        cancha = self._get_cancha_propia(pk, request.user)
        form = CanchaForm(request.POST, request.FILES, instance=cancha)
        if form.is_valid():
            form.save()
            messages.success(request, f'¡Cancha "{cancha.nombre}" actualizada!')
            return redirect('canchas:detalle', pk=cancha.pk)

        return render(request, 'canchas/cancha_form.html', {'form': form, 'cancha': cancha})


class CanchaDeleteView(RoleRequiredMixin, View):
    """Confirmación y eliminación de una cancha propia."""
    allowed_roles = ['DUEÑO']

    def get(self, request, pk):
        cancha = get_object_or_404(Cancha, pk=pk)
        services.verificar_propiedad(cancha, request.user)
        return render(request, 'canchas/cancha_confirm_delete.html', {'cancha': cancha})

    def post(self, request, pk):
        cancha = get_object_or_404(Cancha, pk=pk)
        services.verificar_propiedad(cancha, request.user)
        nombre = cancha.nombre
        cancha.delete()
        messages.success(request, f'Cancha "{nombre}" eliminada correctamente.')
        return redirect('canchas:lista')

from django.http import JsonResponse
from .models import Disponibilidad
from .forms import DisponibilidadForm

class GestionarDisponibilidadView(RoleRequiredMixin, View):
    """Permite al DUEÑO definir la disponibilidad repetitiva de su cancha."""
    allowed_roles = ['DUEÑO']

    def get(self, request, pk):
        cancha = get_object_or_404(Cancha, pk=pk)
        services.verificar_propiedad(cancha, request.user)
        disponibilidades = cancha.disponibilidades.all().order_by('dia_semana', 'hora_inicio')
        form = DisponibilidadForm()
        return render(request, 'canchas/gestionar_disponibilidad.html', {
            'cancha': cancha,
            'disponibilidades': disponibilidades,
            'form': form
        })

    def post(self, request, pk):
        cancha = get_object_or_404(Cancha, pk=pk)
        services.verificar_propiedad(cancha, request.user)

        # Manejar eliminación
        if 'delete_id' in request.POST:
            disp_id = request.POST.get('delete_id')
            cancha.disponibilidades.filter(id=disp_id).delete()
            messages.success(request, 'Disponibilidad eliminada exitosamente.')
            return redirect('canchas:disponibilidad', pk=pk)

        form = DisponibilidadForm(request.POST)
        if form.is_valid():
            disp = form.save(commit=False)
            disp.cancha = cancha
            try:
                disp.save()
                messages.success(request, 'Horario de disponibilidad agregado.')
            except Exception as e:
                messages.error(request, 'Ese horario ya existe o hay un conflicto.')
            return redirect('canchas:disponibilidad', pk=pk)

        disponibilidades = cancha.disponibilidades.all().order_by('dia_semana', 'hora_inicio')
        return render(request, 'canchas/gestionar_disponibilidad.html', {
            'cancha': cancha,
            'disponibilidades': disponibilidades,
            'form': form
        })


class DisponibilidadSlotsView(View):
    """Endpoint AJAX que retorna Array de strings HH:MM de slots disponibles."""

    def get(self, request, pk):
        fecha = request.GET.get('fecha')
        if not fecha:
            return JsonResponse({'error': 'Falta parámetro fecha YYYY-MM-DD'}, status=400)

        try:
            slots = services.obtener_slots_disponibles(pk, fecha)
            slots_str = [slot.strftime('%H:%M') for slot in slots]
            return JsonResponse({'slots': slots_str})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


# ===== FASE 11: CALIFICACIONES =====

class CalificarCanchaView(View):
    """Vista para que un usuario califique una cancha (solo POST).

    Validaciones:
    - Usuario debe estar autenticado
    - Usuario debe haber completado una reserva en esa cancha
    - No existe calificación previa del usuario para la cancha
    - Puntuación debe ser 1-5

    Flujo:
        POST /canchas/<pk>/calificar/
            puntuacion: int (1-5)
            comentario: str opcional

        → Redirige a cancha_detail con mensaje de éxito o error
    """

    def post(self, request, pk):
        """Registra una calificación para la cancha.

        Args:
            request: HttpRequest con POST parameters:
                - puntuacion: int (1-5) requerido
                - comentario: str opcional
            pk: ID de la cancha

        Returns:
            Redirect a cancha_detail con mensaje
        """
        cancha = get_object_or_404(Cancha, pk=pk)

        # Requiere autenticación
        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión para calificar.')
            return redirect('login')

        puntuacion = request.POST.get('puntuacion')
        comentario = request.POST.get('comentario', '')

        # Validar que esté el campo
        if not puntuacion:
            messages.error(request, 'Debes seleccionar una puntuación.')
            return redirect('canchas:detalle', pk=pk)

        try:
            puntuacion = int(puntuacion)

            # Usar service layer
            services.crear_calificacion(
                usuario=request.user,
                cancha=cancha,
                puntuacion=puntuacion,
                comentario=comentario
            )

            messages.success(
                request,
                f'✅ ¡Gracias por calificar {cancha.nombre}! Tu reseña fue publicada.'
            )
        except PermissionDenied as e:
            messages.error(request, f'❌ {str(e)}')
        except Exception as e:  # ValidationError u otro
            messages.error(request, f'❌ Error: {str(e)}')

        return redirect('canchas:detalle', pk=pk)

import csv
from django.http import HttpResponse

class ReporteCanchasView(View):
    """Genera un reporte CSV de las canchas basado en los filtros actuales."""
    
    def get(self, request):
        canchas = Cancha.objects.select_related('deporte', 'dueño').all()
        deporte_id = request.GET.get('deporte')
        q = request.GET.get('q')
        min_precio = request.GET.get('min_precio')
        max_precio = request.GET.get('max_precio')

        if deporte_id:
            canchas = canchas.filter(deporte__id=deporte_id)
        if q:
            canchas = canchas.filter(nombre__icontains=q)
        if min_precio:
            try: canchas = canchas.filter(precio__gte=float(min_precio))
            except ValueError: pass
        if max_precio:
            try: canchas = canchas.filter(precio__lte=float(max_precio))
            except ValueError: pass

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reporte_canchas.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Nombre', 'Deporte', 'Precio', 'Dueño'])

        for c in canchas:
            writer.writerow([c.id, c.nombre, c.deporte.nombre if c.deporte else 'N/A', c.precio, c.dueño.email if c.dueño else 'N/A'])

        return response
