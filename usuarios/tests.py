# usuarios/tests.py
"""Tests de registro de usuarios."""
from django.test import TestCase, Client
from django.urls import reverse
from usuarios.models import CustomUser


class RegistroViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('usuarios:registro')
        self.datos_validos = {
            'username': 'nuevo_user',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan@test.com',
            'rol': 'DEPORTISTA',
            'password1': 'ClaveSegura123!',
            'password2': 'ClaveSegura123!',
        }

    def test_get_muestra_formulario(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Crear cuenta')

    def test_registro_exitoso_redirige_a_login(self):
        response = self.client.post(self.url, self.datos_validos)
        self.assertRedirects(response, reverse('login'))
        self.assertEqual(CustomUser.objects.count(), 1)

    def test_rol_deportista_se_guarda_correctamente(self):
        self.client.post(self.url, self.datos_validos)
        user = CustomUser.objects.get(username='nuevo_user')
        self.assertEqual(user.rol, 'DEPORTISTA')

    def test_rol_dueño_se_guarda_correctamente(self):
        datos = {**self.datos_validos, 'rol': 'DUEÑO', 'username': 'dueno_user', 'email': 'dueno@test.com'}
        self.client.post(self.url, datos)
        user = CustomUser.objects.get(username='dueno_user')
        self.assertEqual(user.rol, 'DUEÑO')

    def test_email_duplicado_falla(self):
        """Edge case: mismo email no puede registrarse dos veces."""
        self.client.post(self.url, self.datos_validos)
        datos2 = {**self.datos_validos, 'username': 'otro_user'}
        response = self.client.post(self.url, datos2)
        self.assertEqual(CustomUser.objects.count(), 1)
        self.assertContains(response, 'ya está registrado')

    def test_username_duplicado_falla(self):
        """Edge case: username único."""
        self.client.post(self.url, self.datos_validos)
        datos2 = {**self.datos_validos, 'email': 'otro@test.com'}
        response = self.client.post(self.url, datos2)
        self.assertEqual(CustomUser.objects.count(), 1)

    def test_passwords_no_coinciden_falla(self):
        """Edge case: confirmación de contraseña incorrecta."""
        datos = {**self.datos_validos, 'password2': 'OtraClave456!'}
        response = self.client.post(self.url, datos)
        self.assertEqual(CustomUser.objects.count(), 0)

    def test_campos_requeridos_vacios_falla(self):
        """Edge case: formulario vacío no crea usuario."""
        response = self.client.post(self.url, {})
        self.assertEqual(CustomUser.objects.count(), 0)
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


class PasswordResetFlowTest(TestCase):
    """Tests de integración para el flujo completo de reset de contraseña.

    Cubre: solicitud, email enviado, confirmación con token válido/inválido,
    y edge cases de tokens expirados o mal formados.
    """

    def setUp(self):
        self.client = Client()
        self.usuario = CustomUser.objects.create_user(
            username='reset_user',
            email='reset@test.com',
            password='ClaveOriginal123!',
            rol='DEPORTISTA'
        )

    def test_formulario_reset_carga_correctamente(self):
        """GET a password_reset retorna 200 con formulario."""
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)

    def test_email_registrado_redirige_a_done(self):
        """POST con email válido redirige a password_reset_done."""
        response = self.client.post(
            reverse('password_reset'),
            {'email': 'reset@test.com'}
        )
        self.assertRedirects(response, reverse('password_reset_done'))

    def test_email_no_registrado_igual_redirige_a_done(self):
        """Edge case: email inexistente no revela si está registrado (seguridad)."""
        response = self.client.post(
            reverse('password_reset'),
            {'email': 'noexiste@test.com'}
        )
        self.assertRedirects(response, reverse('password_reset_done'))

    def test_email_vacio_no_redirige(self):
        """Edge case: email vacío muestra error en el formulario."""
        response = self.client.post(reverse('password_reset'), {'email': ''})
        self.assertEqual(response.status_code, 200)

    def test_token_valido_muestra_formulario_nueva_clave(self):
        """Con uid y token válidos, se muestra el formulario de nueva contraseña."""
        uid = urlsafe_base64_encode(force_bytes(self.usuario.pk))
        token = default_token_generator.make_token(self.usuario)
        url = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_token_invalido_muestra_mensaje_de_error(self):
        """Edge case: token inválido no permite cambiar contraseña."""
        uid = urlsafe_base64_encode(force_bytes(self.usuario.pk))
        url = reverse('password_reset_confirm', kwargs={
            'uidb64': uid,
            'token': 'token-completamente-invalido'
        })
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'inválido')

    def test_nueva_clave_exitosa_redirige_a_complete(self):
        """Con token válido, cambiar la contraseña redirige a password_reset_complete."""
        uid = urlsafe_base64_encode(force_bytes(self.usuario.pk))
        token = default_token_generator.make_token(self.usuario)

        # Primer GET para obtener la cookie de sesión del token
        confirm_url = reverse('password_reset_confirm', kwargs={
            'uidb64': uid, 'token': token
        })
        self.client.get(confirm_url, follow=True)

        # POST con nueva contraseña
        response = self.client.post(confirm_url, {
            'new_password1': 'NuevaClave456!',
            'new_password2': 'NuevaClave456!',
        }, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_claves_no_coinciden_no_cambia_password(self):
        """Edge case: confirmación de contraseña incorrecta no persiste cambios."""
        uid = urlsafe_base64_encode(force_bytes(self.usuario.pk))
        token = default_token_generator.make_token(self.usuario)
        confirm_url = reverse('password_reset_confirm', kwargs={
            'uidb64': uid, 'token': token
        })
        self.client.get(confirm_url, follow=True)

        self.client.post(confirm_url, {
            'new_password1': 'NuevaClave456!',
            'new_password2': 'ClaveDistinta789!',
        })

        # Verificar que la contraseña original sigue funcionando
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('ClaveOriginal123!'))


class PerfilUpdateViewTest(TestCase):
    """Tests para asegurar que la vista de actualización de perfil funcione correctamente."""
    def setUp(self):
        self.client = Client()
        self.usuario = CustomUser.objects.create_user(
            username='perfil_user',
            email='perfil@test.com',
            first_name='Original',
            last_name='Original',
            password='ClaveSegura123!',
            rol='DEPORTISTA'
        )
        self.otro_usuario = CustomUser.objects.create_user(
            username='otro_user',
            email='otro@test.com',
            password='ClaveSegura123!'
        )
        self.url = reverse('usuarios:perfil')

    def test_perfil_requiere_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_perfil_get(self):
        self.client.login(username='perfil_user', password='ClaveSegura123!')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Original')

    def test_perfil_post_exitoso(self):
        self.client.login(username='perfil_user', password='ClaveSegura123!')
        response = self.client.post(self.url, {
            'first_name': 'Nuevo',
            'last_name': 'Nombre',
            'email': 'nuevo@test.com'
        })
        self.assertRedirects(response, self.url)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.first_name, 'Nuevo')
        self.assertEqual(self.usuario.email, 'nuevo@test.com')

    def test_perfil_email_duplicado(self):
        self.client.login(username='perfil_user', password='ClaveSegura123!')
        response = self.client.post(self.url, {
            'first_name': 'Nuevo',
            'last_name': 'Nombre',
            'email': 'otro@test.com' # Email de otro_usuario
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Este correo ya está en uso por otra cuenta.')


class CustomPasswordChangeViewTest(TestCase):
    """Tests para el cambio de contraseñas de sesión activa."""
    def setUp(self):
        self.client = Client()
        self.usuario = CustomUser.objects.create_user(
            username='pass_user',
            password='ClaveSegura123!',
        )
        self.url = reverse('usuarios:cambiar_password')

    def test_password_change_requiere_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_password_change_get(self):
        self.client.login(username='pass_user', password='ClaveSegura123!')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_password_change_post_exitoso(self):
        self.client.login(username='pass_user', password='ClaveSegura123!')
        response = self.client.post(self.url, {
            'old_password': 'ClaveSegura123!',
            'new_password1': 'NuevaClave456!',
            'new_password2': 'NuevaClave456!',
        })
        self.assertRedirects(response, reverse('usuarios:perfil'))
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('NuevaClave456!'))
