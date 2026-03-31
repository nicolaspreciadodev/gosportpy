from django.test import TestCase
from django.core import mail
from core.emails import (
    enviar_confirmacion_reserva,
    enviar_recordatorio_reserva,
    enviar_notificacion_inscripcion_equipo,
    enviar_notificacion_torneo_aprobado
)
from canchas.models import Cancha, Deporte
from negocio.models import Reserva, Torneo, Equipo
from usuarios.models import CustomUser
from django.utils import timezone

class EmailServiceTests(TestCase):
    def setUp(self):
        self.dueno = CustomUser.objects.create_user(username='dueno', email='dueno@test.com', password='pw', rol='DUEÑO', first_name='Juan')
        self.deportista = CustomUser.objects.create_user(username='deporta', email='deporta@test.com', password='pw', rol='DEPORTISTA', first_name='Carlos')
        self.deporte = Deporte.objects.create(nombre='Futbol')
        self.cancha = Cancha.objects.create(nombre='Cancha 1', deporte=self.deporte, precio=50000, dueño=self.dueno)
        
        self.reserva = Reserva.objects.create(
            usuario=self.deportista,
            cancha=self.cancha,
            fecha=timezone.localdate(),
            hora='14:00'
        )
        
        self.torneo = Torneo.objects.create(
            nombre='Champions Test',
            organizador=self.dueno,
            deporte=self.deporte,
            fecha_inicio=timezone.localdate(),
            fecha_fin=timezone.localdate(),
            max_equipos=4,
            formato='LIGA',
            estado='PUBLICADO'
        )
        
        self.equipo = Equipo.objects.create(nombre='Los Tigres')
        self.equipo.jugadores.add(self.deportista)

    def test_enviar_confirmacion_reserva(self):
        enviar_confirmacion_reserva(self.reserva)
        # Should send 2 emails: One to deportista, One to dueno
        self.assertEqual(len(mail.outbox), 2)
        
        mail_deportista = mail.outbox[0]
        self.assertEqual(mail_deportista.to, ['deporta@test.com'])
        self.assertIn('Confirmación de Reserva', mail_deportista.subject)
        
        mail_dueno = mail.outbox[1]
        self.assertEqual(mail_dueno.to, ['dueno@test.com'])
        self.assertIn('Nueva Reserva', mail_dueno.subject)

    def test_enviar_recordatorio_reserva(self):
        enviar_recordatorio_reserva(self.reserva)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['deporta@test.com'])
        self.assertIn('Recordatorio de Reserva', mail.outbox[0].subject)

    def test_enviar_notificacion_torneo_aprobado(self):
        enviar_notificacion_torneo_aprobado(self.torneo)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['dueno@test.com'])
        self.assertIn('Tu Torneo ha sido Aprobado', mail.outbox[0].subject)
        
    def test_enviar_notificacion_inscripcion_equipo(self):
        enviar_notificacion_inscripcion_equipo(self.torneo, self.equipo)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['dueno@test.com'])
        self.assertIn('Nuevo Equipo Inscrito', mail.outbox[0].subject)
