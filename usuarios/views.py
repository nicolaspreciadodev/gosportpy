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
            writer.writerow([u.id, u.email, u.nombre, u.apellido, getattr(u, 'rol', 'N/A'), u.date_joined.strftime("%Y-%m-%d")])

        return response
