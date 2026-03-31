from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from negocio.models import Torneo, Equipo, Partido, PosicionEquipo
from negocio.services import generar_fixture_liga, registrar_resultado
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator

@method_decorator(user_passes_test(lambda u: u.is_staff), name='dispatch')
class AprobarTorneoView(LoginRequiredMixin, View):
    """Vista para que un ADMINISTRADOR apruebe o rechace un torneo."""
    def post(self, request, torneo_id):
        torneo = get_object_or_404(Torneo, id=torneo_id)
        accion = request.POST.get('accion')

        if accion == 'aprobar':
            torneo.estado = 'PUBLICADO'
            
            try:
                from core.emails import enviar_notificacion_torneo_aprobado
                enviar_notificacion_torneo_aprobado(torneo)
            except Exception as ex:
                pass
                
            messages.success(request, f'El torneo "{torneo.nombre}" ha sido aprobado y publicado.')
        elif accion == 'rechazar':
            torneo.estado = 'PENDIENTE'
            torneo.is_approved = False
            messages.warning(request, f'El torneo "{torneo.nombre}" ha sido rechazado.')
        else:
            messages.error(request, 'Acción no válida.')
            return redirect('dashboard')

        torneo.save()
        return redirect('dashboard')


class InscribirEquipoView(LoginRequiredMixin, View):
    """Vista para que un miembro de un equipo inscriba al equipo en un torneo."""
    def post(self, request, torneo_id):
        torneo = get_object_or_404(Torneo, id=torneo_id)
        equipo_id = request.POST.get('equipo_id')

        if not equipo_id:
            messages.error(request, 'Debe seleccionar un equipo válido.')
            return redirect('dashboard')

        equipo = get_object_or_404(Equipo, id=equipo_id)

        if request.user not in equipo.jugadores.all():
            messages.error(request, 'No tienes permiso para inscribir este equipo.')
            return redirect('dashboard')

        if torneo.estado != 'PUBLICADO':
            messages.error(request, 'El torneo no está abierto para inscripciones.')
            return redirect('dashboard')

        if equipo.torneos.filter(id=torneo.id).exists():
            messages.error(request, 'Tu equipo ya está inscrito en este torneo.')
            return redirect('dashboard')

        equipo.torneos.add(torneo)
        
        try:
            from core.emails import enviar_notificacion_inscripcion_equipo
            enviar_notificacion_inscripcion_equipo(torneo, equipo)
        except Exception as ex:
            pass
            
        messages.success(request, f'¡El equipo {equipo.nombre} ha sido inscrito exitosamente!')
        return redirect('dashboard')


from typing import Dict, List

class TorneoDetalleView(LoginRequiredMixin, View):
    """Vista pública para ver el detalle de un torneo, tabla de posiciones y fixture."""
    def get(self, request, pk):
        torneo = get_object_or_404(Torneo, id=pk)
        posiciones = PosicionEquipo.objects.filter(torneo=torneo)
        partidos = Partido.objects.filter(torneo=torneo)

        jornadas: Dict[int, List[Partido]] = {}
        for partido in partidos:
            jornadas.setdefault(partido.jornada, []).append(partido)

        return render(request, 'negocio/torneo_detalle.html', {
            'torneo': torneo,
            'posiciones': posiciones,
            'jornadas': sorted(jornadas.items())
        })


class GenerarFixtureView(LoginRequiredMixin, View):
    """Vista para generar el fixture de un torneo (solo organizador)."""
    def post(self, request, pk):
        torneo = get_object_or_404(Torneo, id=pk)

        if request.user != torneo.organizador:
            messages.error(request, 'Solo el organizador puede generar el fixture.')
            return redirect('negocio:torneo_detalle', pk=torneo.id)

        try:
            generar_fixture_liga(torneo)
            messages.success(request, '✅ Fixture generado exitosamente.')
        except ValidationError as e:
            messages.error(request, f'❌ Error: {e.message}')

        return redirect('negocio:torneo_detalle', pk=torneo.id)


class RegistrarResultadoView(LoginRequiredMixin, View):
    """Vista para registrar un resultado de partido (solo organizador del torneo)."""
    def post(self, request, pk):
        partido = get_object_or_404(Partido, id=pk)

        goles_local = request.POST.get('goles_local')
        goles_visitante = request.POST.get('goles_visitante')

        if not (goles_local and goles_visitante):
            messages.error(request, '❌ Debe especificar los goles de ambos equipos.')
            return redirect('negocio:torneo_detalle', pk=partido.torneo.id)

        try:
            registrar_resultado(partido, int(goles_local), int(goles_visitante), request.user)
            messages.success(request, f'✅ Resultado registrado. Tabla actualizada.')
        except ValidationError as e:
            messages.error(request, f'❌ Error: {e.message}')
        except ValueError:
            messages.error(request, '❌ Los goles deben ser números enteros.')

        return redirect('negocio:torneo_detalle', pk=partido.torneo.id)
