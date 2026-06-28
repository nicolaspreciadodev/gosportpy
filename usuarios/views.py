# usuarios/views.py
"""Vistas de gestión de usuarios: registro."""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from .forms import RegistroUsuarioForm


class RegistroView:
    """Vista basada en función para el registro de nuevos usuarios.

    Flujo:
        GET  → muestra el formulario vacío.
        POST → valida, crea el usuario y redirige al login con mensaje.

    No usa auto-login post-registro: el usuario debe autenticarse
    manualmente para mayor seguridad y claridad del flujo.
    """

    @staticmethod
    def get(request):
        return render(request, 'registration/register.html', {
            'form': RegistroUsuarioForm()
        })

    @staticmethod
    def post(request):
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                '¡Cuenta creada exitosamente! Inicia sesión para continuar.'
            )
            return redirect('login')

        return render(request, 'registration/register.html', {'form': form})


def registro(request):
    """Entry point de la vista de registro (compatible con urls.py funcional)."""
    view = RegistroView()
    if request.method == 'POST':
        return view.post(request)
    return view.get(request)


from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from .models import CustomUser
from .forms import PerfilForm


class PerfilUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Vista para actualizar datos básicos del perfil de usuario.

    Solo usuarios autenticados pueden acceder.
    Permite editar: nombre, apellido, email.
    Email debe ser único (no puede duplicarse con otro usuario).

    Atributos:
        model: CustomUser
        form_class: PerfilForm
        template_name: usuarios/perfil.html
        success_url: redirige a la misma vista (actualización exitosa)
        success_message: mensaje mostrado al usuario

    Flujo:
        GET  → muestra formulario con datos actuales del usuario
        POST → valida y guarda cambios, redirige con mensaje exitoso

    Raises:
        PermissionDenied: si el usuario intenta acceder sin estar autenticado
    """
    model = CustomUser
    form_class = PerfilForm
    template_name = 'usuarios/perfil.html'
    success_url = reverse_lazy('usuarios:perfil')
    success_message = "Tu perfil ha sido actualizado exitosamente."

    def get_object(self, queryset=None):
        """Retorna siempre el usuario autenticado actual.

        Returns:
            CustomUser: el usuario que realiza la petición
        """
        return self.request.user


class CustomPasswordChangeView(LoginRequiredMixin, SuccessMessageMixin, PasswordChangeView):
    """Vista para cambiar contraseña manteniendo la sesión activa.

    Solo usuarios autenticados pueden acceder.
    Requiere la contraseña anterior para validar la identidad del usuario.
    Mantiene la sesión activa después del cambio.

    Atributos:
        template_name: usuarios/cambiar_password.html
        success_url: redirige a perfil después del cambio exitoso
        success_message: mensaje mostrado al usuario

    Flujo:
        GET  → muestra formulario con campos: contraseña actual, nueva, confirmación
        POST → valida contraseña anterior y cambio exitoso, redirige con mensaje

    Raises:
        PermissionDenied: si el usuario intenta acceder sin estar autenticado

    Diferencias con PasswordResetView:
        - Se usa cuando el usuario RECUERDA su contraseña actual
        - Requiere contraseña anterior como verificación de seguridad
        - La sesión permanece activa (el usuario sigue "logueado")
    """
    template_name = 'usuarios/cambiar_password.html'
    success_url = reverse_lazy('usuarios:perfil')
    success_message = "Tu contraseña ha sido cambiada exitosamente."

import csv
from django.http import HttpResponse
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views import View

class ReporteUsuariosView(UserPassesTestMixin, View):
    """Vista para que un administrador descargue la lista de usuarios."""
    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request):
        usuarios = CustomUser.objects.all().order_by('date_joined')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reporte_usuarios.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Email', 'Nombre', 'Apellido', 'Rol', 'Fecha Registro'])

        for u in usuarios:
            writer.writerow([u.id, u.email, u.first_name, u.last_name, getattr(u, 'rol', 'N/A'), u.date_joined.strftime("%Y-%m-%d")])

        return response

from django.views.generic import ListView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from .models import SolicitudRolDueño
from .forms import SolicitudRolDueñoForm


class AdminUserListView(UserPassesTestMixin, ListView):
    model = CustomUser
    template_name = 'usuarios/admin_user_list.html'
    context_object_name = 'usuarios'

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Número de solicitudes de rol pendientes para mostrar badge
        context['solicitudes_pendientes'] = SolicitudRolDueño.objects.filter(estado='PENDIENTE').count()
        return context


class AdminUserUpdateView(UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = CustomUser
    template_name = 'usuarios/admin_user_form.html'
    fields = ['username', 'first_name', 'last_name', 'email', 'rol', 'is_active', 'is_superuser']
    success_url = reverse_lazy('usuarios:admin_user_list')
    success_message = "Usuario actualizado correctamente."

    def test_func(self):
        return self.request.user.is_superuser


class AdminUserDeleteView(UserPassesTestMixin, DeleteView):
    model = CustomUser
    template_name = 'usuarios/admin_user_confirm_delete.html'
    success_url = reverse_lazy('usuarios:admin_user_list')

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(self.request, "Usuario eliminado correctamente.")
        return redirect(success_url)


# ============================================================
# FLUJO DE SOLICITUD DE ROL DUEÑO
# ============================================================

class SolicitarRolDueñoView(LoginRequiredMixin, View):
    """Vista para que un Deportista solicite convertirse en Dueño de Cancha.

    Reglas:
    - Solo Deportistas pueden acceder (los Dueños ya tienen el rol).
    - Un usuario no puede tener más de una solicitud PENDIENTE activa.
    """
    template_name = 'usuarios/solicitar_rol_dueno.html'

    def dispatch(self, request, *args, **kwargs):
        # Si ya es dueño, redirigir al dashboard
        if request.user.is_authenticated and request.user.rol == 'DUEÑO':
            messages.info(request, 'Ya tienes el rol de Dueño de Cancha.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        solicitud_activa = SolicitudRolDueño.objects.filter(
            usuario=request.user,
            estado='PENDIENTE'
        ).first()
        form = SolicitudRolDueñoForm()
        return render(request, self.template_name, {
            'form': form,
            'solicitud_activa': solicitud_activa,
        })

    def post(self, request):
        # Verificar que no haya una solicitud pendiente previa
        if SolicitudRolDueño.objects.filter(usuario=request.user, estado='PENDIENTE').exists():
            messages.warning(request, 'Ya tienes una solicitud en proceso. Espera la respuesta del administrador.')
            return redirect('usuarios:solicitar_rol_dueno')

        form = SolicitudRolDueñoForm(request.POST)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.usuario = request.user
            solicitud.save()
            messages.success(
                request,
                '¡Solicitud enviada! El administrador revisará tu caso y recibirás una respuesta pronto.'
            )
            return redirect('dashboard')

        return render(request, self.template_name, {'form': form})


class AdminSolicitudesRolView(UserPassesTestMixin, View):
    """Vista para que el SuperAdmin vea y gestione las solicitudes de rol Dueño."""

    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request):
        estado_filter = request.GET.get('estado', 'PENDIENTE')
        solicitudes = SolicitudRolDueño.objects.select_related('usuario').all()
        if estado_filter and estado_filter != 'TODAS':
            solicitudes = solicitudes.filter(estado=estado_filter)

        context = {
            'solicitudes': solicitudes,
            'estado_activo': estado_filter,
            'total_pendientes': SolicitudRolDueño.objects.filter(estado='PENDIENTE').count(),
            'estados_filtro': [
                ('PENDIENTE', '⏳ Pendientes'),
                ('APROBADO', '✅ Aprobadas'),
                ('RECHAZADO', '❌ Rechazadas'),
                ('TODAS', '📋 Todas'),
            ],
        }
        return render(request, 'usuarios/admin_solicitudes_rol.html', context)


class AdminAprobarSolicitudView(UserPassesTestMixin, View):
    """Aprueba una solicitud de rol Dueño y cambia el rol del usuario."""

    def test_func(self):
        return self.request.user.is_superuser

    def post(self, request, pk):
        from django.shortcuts import get_object_or_404
        solicitud = get_object_or_404(SolicitudRolDueño, pk=pk)

        if solicitud.estado != 'PENDIENTE':
            messages.error(request, 'Esta solicitud ya fue procesada.')
            return redirect('usuarios:admin_solicitudes_rol')

        # Cambiar el rol del usuario
        solicitud.usuario.rol = 'DUEÑO'
        solicitud.usuario.save()

        # Marcar solicitud como aprobada
        solicitud.estado = 'APROBADO'
        solicitud.fecha_respuesta = timezone.now()
        solicitud.notas_admin = request.POST.get('notas_admin', '')
        solicitud.save()

        messages.success(
            request,
            f'✅ Solicitud de {solicitud.usuario.username} aprobada. El usuario ahora es Dueño de Cancha.'
        )
        return redirect('usuarios:admin_solicitudes_rol')


class AdminRechazarSolicitudView(UserPassesTestMixin, View):
    """Rechaza una solicitud de rol Dueño."""

    def test_func(self):
        return self.request.user.is_superuser

    def post(self, request, pk):
        from django.shortcuts import get_object_or_404
        solicitud = get_object_or_404(SolicitudRolDueño, pk=pk)

        if solicitud.estado != 'PENDIENTE':
            messages.error(request, 'Esta solicitud ya fue procesada.')
            return redirect('usuarios:admin_solicitudes_rol')

        solicitud.estado = 'RECHAZADO'
        solicitud.fecha_respuesta = timezone.now()
        solicitud.notas_admin = request.POST.get('notas_admin', 'Solicitud no aprobada por el administrador.')
        solicitud.save()

        messages.warning(
            request,
            f'❌ Solicitud de {solicitud.usuario.username} rechazada.'
        )
        return redirect('usuarios:admin_solicitudes_rol')
