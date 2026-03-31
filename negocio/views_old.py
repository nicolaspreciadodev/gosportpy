from urllib import request

from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins import RoleRequiredMixin
from django.contrib import messages
from canchas.models import Cancha
from .models import Reserva, Factura, Torneo, Equipo, Partido, PosicionEquipo
from .services import generar_fixture_liga, registrar_resultado
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator


@method_decorator(user_passes_test(lambda u: u.is_staff), name='dispatch')
class AprobarTorneoView(LoginRequiredMixin, View):
    """Vista para que un ADMINISTRADOR apruebe o rechace un torneo."""

    def post(self, request, torneo_id):
        torneo = get_object_or_404(Torneo, id=torneo_id)
        accion = request.POST.get('accion')  # 'aprobar' o 'rechazar'

        if accion == 'aprobar':
            torneo.estado = 'PUBLICADO'
            messages.success(request, f'El torneo "{torneo.nombre}" ha sido aprobado y publicado.')
        elif accion == 'rechazar':
            torneo.estado = 'PENDIENTE'
            torneo.is_approved = False
            messages.warning(request, f'El torneo "{torneo.nombre}" ha sido rechazado.')
        else:
            messages.error(request, 'Acción no válida.')
            return redirect('dashboard') # O a la página de detalle del torneo

        torneo.save()
        return redirect('dashboard') # Redirigir a una página de administración de torneos o dashboard


class CrearReservaView(RoleRequiredMixin, View):
    """Vista para que un DEPORTISTA cree una reserva en una cancha."""
    allowed_roles = ['DEPORTISTA']

    def get(self, request, cancha_id):
        cancha = get_object_or_404(Cancha, id=cancha_id)
        return render(request, 'crear_reserva.html', {'cancha': cancha})

    def post(self, request, cancha_id):
        cancha = get_object_or_404(Cancha, id=cancha_id)
        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora')

        if not fecha or not hora:
            messages.error(request, 'Debe proporcionar una fecha y hora.')
            return render(request, 'crear_reserva.html', {'cancha': cancha})

        from canchas.services import validar_slot_disponible
        if not validar_slot_disponible(cancha_id, fecha, hora):
            messages.error(request, 'El horario seleccionado no está disponible o es inválido.')
            return render(request, 'crear_reserva.html', {'cancha': cancha})

        reserva = Reserva(usuario=request.user, cancha=cancha, fecha=fecha, hora=hora)

        try:
            reserva.full_clean()
            reserva.save()
            messages.success(request, '¡Reserva creada con éxito!')
            return redirect('dashboard')
        except ValidationError as e:
            for msg in e.messages:
                messages.error(request, msg)
            return render(request, 'crear_reserva.html', {'cancha': cancha})


class FacturaDetalleView(LoginRequiredMixin, View):
    """Vista para que un usuario vea el detalle de su factura.

    Solo el dueño de la reserva puede ver su factura (evita acceso cruzado).
    """

    def get(self, request, factura_id):
        factura = get_object_or_404(Factura, id=factura_id)
        reserva = factura.reserva

        # 🔒 Solo el propietario de la reserva puede ver su factura
        if reserva.usuario != request.user:
            messages.error(request, 'No tienes permiso para ver esta factura.')
            return redirect('dashboard')

        return render(request, 'factura_detalle.html', {
            'factura': factura,
            'reserva': reserva,
        })

class CancelarReservaView(LoginRequiredMixin, View):
    """Vista para que un DEPORTISTA o DUEÑO cancele una reserva si cumple las reglas."""
    def post(self, request, reserva_id):
        reserva = get_object_or_404(Reserva, id=reserva_id)

        # Solo el dueño de la reserva o el dueño de la cancha pueden cancelarla
        es_dueno_reserva = reserva.usuario == request.user
        es_dueno_cancha = reserva.cancha.dueño == request.user

        if not (es_dueno_reserva or es_dueno_cancha):
            messages.error(request, 'No tienes permiso para cancelar esta reserva.')
            return redirect('dashboard')

        if reserva.estado == 'CANCELADA':
            messages.error(request, 'Esta reserva ya se encuentra cancelada.')
            return redirect('dashboard')

        if reserva.estado == 'COMPLETADA':
            messages.error(request, 'Esta reserva ya se completó, no puede ser cancelada.')
            return redirect('dashboard')

        # Si es el deportista, validamos las 24 horas. El dueño puede obviar esto, o también aplicamos regla general.
        # Aplicamos la regla a todos según el requisito.
        if not reserva.puede_cancelar():
            messages.error(request, 'Solo puedes cancelar con al menos 24 horas de anticipación.')
            return redirect('dashboard')

        # Si todo es válido
        reserva.estado = 'CANCELADA'
        reserva.save()
        messages.success(request, 'La reserva ha sido cancelada exitosamente y el horario fue liberado.')
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

        # Validar permisos: el usuario debe pertenecer al equipo
        if request.user not in equipo.jugadores.all():
            messages.error(request, 'No tienes permiso para inscribir este equipo, ya que no perteneces a sus jugadores.')
            return redirect('dashboard')

        # Validar que el torneo esté publicado
        if torneo.estado != 'PUBLICADO':
            messages.error(request, 'El torneo no está abierto para inscripciones.')
            return redirect('dashboard')

        # Validar si el equipo ya está inscrito
        if equipo.torneos.filter(id=torneo.id).exists():
            messages.error(request, 'Tu equipo ya está inscrito en este torneo.')
            return redirect('dashboard')

        # Realizar inscripción
        equipo.torneos.add(torneo)
        messages.success(request, f'¡El equipo {equipo.nombre} ha sido inscrito en el torneo {torneo.nombre} exitosamente!')
        return redirect('dashboard')


class PanelReservasView(RoleRequiredMixin, View):
    """Vista para que el DUEÑO vea y filtre las reservas de TODAS sus canchas."""
    allowed_roles = ['DUEÑO']

    def get(self, request):
        canchas_dueño = Cancha.objects.filter(dueño=request.user)
        reservas = Reserva.objects.filter(cancha__in=canchas_dueño).order_by('-fecha', '-hora')

        # Filtros
        estado_filter = request.GET.get('estado')
        if estado_filter:
            reservas = reservas.filter(estado=estado_filter)

        fecha_filter = request.GET.get('fecha')
        if fecha_filter:
            reservas = reservas.filter(fecha=fecha_filter)

        cancha_filter = request.GET.get('cancha_id')
        if cancha_filter:
            try:
                reservas = reservas.filter(cancha__id=int(cancha_filter))
            except ValueError:
                pass

        context = {
            'reservas': reservas,
            'estado_activo': estado_filter,
            'fecha_activa': fecha_filter,
            'cancha_activa': cancha_filter,
            'canchas': canchas_dueño,
        }
        return render(request, 'panel_reservas.html', context)


class SimularPagoView(LoginRequiredMixin, View):
    """Vista para simular el pago de una reserva."""
    def post(self, request, reserva_id):
        reserva = get_object_or_404(Reserva, id=reserva_id)

        # Solo el dueño de la reserva puede pagarla
        if reserva.usuario != request.user:
            messages.error(request, 'No tienes permiso para pagar esta reserva.')
            return redirect('dashboard')

        if reserva.pagado:
            messages.warning(request, 'Esta reserva ya se encuentra pagada.')
            return redirect('dashboard')

        if reserva.estado != 'PROGRAMADA':
            messages.error(request, 'Solo las reservas programadas pueden ser pagadas.')
            return redirect('dashboard')

        # Simular pago exitoso
        reserva.pagado = True
        reserva.save()

        messages.success(request, '¡El pago ha sido procesado exitosamente!')
        return redirect('negocio:factura_detalle', factura_id=reserva.factura.id)

class TorneoDetalleView(LoginRequiredMixin, View):
    """Vista pública para ver el detalle de un torneo, tabla de posiciones y fixture.

    Muestra:
        - Información del torneo (nombre, descripción, formato, estado)
        - Tabla de posiciones (PJ, PG, PE, PP, GF, GC, Pts)
        - Fixture agrupado por jornadas con resultados
        - Botón para generar fixture (solo organizador, si no está generado)
        - Formulario modal para registrar resultados (solo organizador)

    Atributos:
        model: Torneo
        template_name: negocio/torneo_detalle.html

    Flujo:
        GET /torneos/<id>/ → carga torneo, posiciones, partidos agrupados por jornada
    """

    def get(self, request, pk):
        """Renderiza detalle del torneo con tabla de posiciones y fixture.

        Args:
            request: HttpRequest del usuario
            pk: ID del torneo

        Returns:
            HttpResponse con template torneo_detalle.html
        """
        torneo = get_object_or_404(Torneo, id=pk)
        posiciones = PosicionEquipo.objects.filter(torneo=torneo)
        partidos = Partido.objects.filter(torneo=torneo)

        # Agrupar partidos por jornada para el template
        jornadas = {}
        for partido in partidos:
            jornadas.setdefault(partido.jornada, []).append(partido)

        return render(request, 'negocio/torneo_detalle.html', {
            'torneo': torneo,
            'posiciones': posiciones,
            'jornadas': sorted(jornadas.items())
        })


class GenerarFixtureView(LoginRequiredMixin, View):
    """Vista para generar el fixture de un torneo (solo organizador).

    Genera el calendario de partidos usando algoritmo Round-Robin para formato LIGA.
    También inicializa la tabla de posiciones de todos los equipos.

    Validaciones:
        - Solo el organizador puede generar fixture
        - Se necesitan al menos 2 equipos inscritos
        - El fixture no puede ser generado dos veces
        - Solo funciona para formato LIGA

    Atributos:
        required_permission: organizador del torneo

    Flujo:
        POST /torneos/<id>/generar-fixture/ → genera fixture y redirige a detalle
    """

    def post(self, request, pk):
        """Genera el fixture del torneo válido con todo chequeo.

        Args:
            request: HttpRequest del usuario
            pk: ID del torneo

        Returns:
            Redirect a torneo_detalle con mensaje de exito o error
        """
        torneo = get_object_or_404(Torneo, id=pk)

        if request.user != torneo.organizador:
            messages.error(request, 'Solo el organizador puede generar el fixture.')
            return redirect('negocio:torneo_detalle', pk=torneo.id)

        try:
            generar_fixture_liga(torneo)
            messages.success(request, '✅ Fixture generado exitosamente. Los partidos están listos para comenzar.')
        except ValidationError as e:
            messages.error(request, f'❌ Error: {e.message}')

        return redirect('negocio:torneo_detalle', pk=torneo.id)


class RegistrarResultadoView(LoginRequiredMixin, View):
    """Vista para registrar un resultado de partido (solo organizador del torneo).

    Registra los goles de ambos equipos y dispara la actualización automática
    de la tabla de posiciones.

    Validaciones:
        - Solo el organizador del torneo puede registrar
        - El partido no puede tener resultado registrado dos veces
        - Los goles deben ser números enteros no negativos

    Atributos:
        required_permission: organizador del torneo

    Flujo:
        POST /partidos/<id>/resultado/
            - goles_local (int): goles del equipo local
            - goles_visitante (int): goles del equipo visitante
        → actualiza Partido, Table de Posiciones, redirige a torneo_detalle
    """

    def post(self, request, pk):
        """Registra resultados del partido y actualiza tabla de posiciones.

        Args:
            request: HttpRequest con POST parameters:
                - goles_local: int >= 0
                - goles_visitante: int >= 0
            pk: ID del partido

        Returns:
            Redirect a torneo_detalle con mensaje de éxito o error
        """
        partido = get_object_or_404(Partido, id=pk)

        goles_local = request.POST.get('goles_local')
        goles_visitante = request.POST.get('goles_visitante')

        if not (goles_local and goles_visitante):
            messages.error(request, '❌ Debe especificar los goles de ambos equipos.')
            return redirect('negocio:torneo_detalle', pk=partido.torneo.id)

        try:
            registrar_resultado(partido, int(goles_local), int(goles_visitante), request.user)
            messages.success(request, f'✅ Resultado registrado: {partido.equipo_local.nombre} {goles_local}-{goles_visitante} {partido.equipo_visitante.nombre}. Tabla actualizada.')
        except ValidationError as e:
            messages.error(request, f'❌ Error: {e.message}')
        except ValueError:
            messages.error(request, '❌ Los goles deben ser números enteros.')

        return redirect('negocio:torneo_detalle', pk=partido.torneo.id)

import csv
from django.http import HttpResponse

class ReporteReservasView(RoleRequiredMixin, View):
    allowed_roles = ['DUEÑO']
    def get(self, request):
        canchas_dueño = Cancha.objects.filter(dueño=request.user)
        reservas = Reserva.objects.filter(cancha__in=canchas_dueño).order_by('-fecha', '-hora')

        estado_filter = request.GET.get('estado')
        if estado_filter:
            reservas = reservas.filter(estado=estado_filter)

        fecha_filter = request.GET.get('fecha')
        if fecha_filter:
            reservas = reservas.filter(fecha=fecha_filter)

        cancha_filter = request.GET.get('cancha_id')
        if cancha_filter:
            try:
                reservas = reservas.filter(cancha__id=int(cancha_filter))
            except ValueError:
                pass

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reporte_reservas.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Cancha', 'Deportista', 'Fecha', 'Hora', 'Estado', 'Pagado'])

        for r in reservas:
            writer.writerow([r.id, r.cancha.nombre, r.usuario.email, r.fecha, r.hora, r.estado, 'Sí' if r.pagado else 'No'])

        return response

class ReporteTorneosView(RoleRequiredMixin, View):
    allowed_roles = ['DUEÑO']
    def get(self, request):
        torneos = Torneo.objects.filter(organizador=request.user).order_by('-fecha_inicio')

        torneo_q = request.GET.get('torneo_q')
        if torneo_q:
            torneos = torneos.filter(nombre__icontains=torneo_q)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reporte_torneos.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Nombre', 'Deporte', 'Estado', 'Equipos Inscritos', 'Max Equipos'])

        for t in torneos:
            writer.writerow([t.id, t.nombre, t.deporte.nombre, t.estado, t.equipos.count(), t.max_equipos])

        return response
