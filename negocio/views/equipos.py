from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from core.mixins import RoleRequiredMixin
from negocio.models import Equipo
from negocio.forms import EquipoForm
from django.contrib.auth import get_user_model

User = get_user_model()

class EquipoCreateView(RoleRequiredMixin, View):
    """Permite crear un equipo deportivo."""
    allowed_roles = ['DEPORTISTA', 'DUEÑO']

    def get(self, request):
        form = EquipoForm()
        # Solo mostrar otros usuarios que sean deportistas
        form.fields['jugadores'].queryset = User.objects.filter(rol='DEPORTISTA').exclude(id=request.user.id)
        return render(request, 'negocio/equipo_form.html', {'form': form})

    def post(self, request):
        form = EquipoForm(request.POST, request.FILES)
        form.fields['jugadores'].queryset = User.objects.filter(rol='DEPORTISTA').exclude(id=request.user.id)
        
        if form.is_valid():
            equipo = form.save(commit=False)
            equipo.save()
            form.save_m2m() # Guarda los jugadores que seleccionó
            
            # El creador es automáticamente jugador
            equipo.jugadores.add(request.user)
            
            messages.success(request, f'¡El equipo {equipo.nombre} ha sido creado!')
            return redirect('negocio:mis_equipos')
        
        return render(request, 'negocio/equipo_form.html', {'form': form})


class MisEquiposView(RoleRequiredMixin, View):
    """Lista los equipos a los que pertenece el usuario."""
    allowed_roles = ['DEPORTISTA', 'DUEÑO']

    def get(self, request):
        equipos = request.user.equipos.all()
        return render(request, 'negocio/mis_equipos.html', {'equipos': equipos})

class EquipoDetailView(RoleRequiredMixin, View):
    """Muestra los detalles de un equipo."""
    allowed_roles = ['DEPORTISTA', 'DUEÑO']

    def get(self, request, pk):
        equipo = get_object_or_404(Equipo, id=pk)
        
        # Opcional: restringir para que solo lo vean los jugadores del equipo o administradores
        if request.user not in equipo.jugadores.all() and not request.user.is_staff:
            messages.error(request, 'No tienes permiso para ver este equipo.')
            return redirect('negocio:mis_equipos')
            
        torneos = equipo.torneos.all()
        return render(request, 'negocio/equipo_detalle.html', {
            'equipo': equipo,
            'torneos': torneos,
        })

