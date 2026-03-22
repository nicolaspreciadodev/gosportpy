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
from . import services


class CanchaListView(View):
    """Lista pública de todas las canchas disponibles.

    Soporta filtrado por deporte vía query param ?deporte=<id>.
    Accesible para cualquier usuario autenticado.
    """

    def get(self, request):
        canchas = Cancha.objects.select_related('deporte', 'dueño').all()
        deporte_id = request.GET.get('deporte')
        if deporte_id:
            canchas = canchas.filter(deporte__id=deporte_id)

        context = {
            'canchas': canchas,
            'deportes': Deporte.objects.all(),
            'deporte_activo': deporte_id,
        }
        return render(request, 'canchas/cancha_list.html', context)


class CanchaDetailView(View):
    """Detalle de una cancha con disponibilidad y botón de reserva."""

    def get(self, request, pk):
        cancha = get_object_or_404(
            Cancha.objects.select_related('deporte', 'dueño'), pk=pk
        )
        return render(request, 'canchas/cancha_detail.html', {'cancha': cancha})


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
