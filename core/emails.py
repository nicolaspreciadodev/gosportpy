from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def enviar_email_base(subject, context, template_name, to_emails):
    """
    Función base para enviar emails HTML utilizando el sistema de templates de Django.
    """
    html_content = render_to_string(template_name, context)
    text_content = strip_tags(html_content)  # Fallback a texto plano
    
    from_email = settings.DEFAULT_FROM_EMAIL
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=to_emails
    )
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)

def enviar_confirmacion_reserva(reserva):
    """
    Envía confirmación de reserva al DEPORTISTA y notificación al DUEÑO.
    """
    context = {
        'reserva': reserva,
        'cancha': reserva.cancha,
        'usuario': reserva.usuario
    }
    
    # 1. Al Deportista
    enviar_email_base(
        subject=f"✅ Confirmación de Reserva: {reserva.cancha.nombre}",
        context=context,
        template_name="emails/reserva_confirmada.html",
        to_emails=[reserva.usuario.email]
    )
    
    # 2. Al Dueño
    enviar_email_base(
        subject=f"📅 Nueva Reserva en tu Cancha: {reserva.cancha.nombre}",
        context=context,
        template_name="emails/nueva_reserva_dueno.html",
        to_emails=[reserva.cancha.dueño.email]
    )

def enviar_recordatorio_reserva(reserva):
    """
    Envía recordatorio de 24h al usuario que hizo la reservación.
    """
    context = {
        'reserva': reserva,
        'cancha': reserva.cancha,
        'usuario': reserva.usuario
    }
    enviar_email_base(
        subject=f"⚡ Recordatorio de Reserva Mañana: {reserva.cancha.nombre}",
        context=context,
        template_name="emails/recordatorio_reserva.html",
        to_emails=[reserva.usuario.email]
    )

def enviar_notificacion_inscripcion_equipo(torneo, equipo):
    """
    Notifica al organizador del torneo que un nuevo equipo se inscribió.
    """
    context = {
        'torneo': torneo,
        'equipo': equipo,
        'organizador': torneo.organizador
    }
    enviar_email_base(
        subject=f"🏆 Nuevo Equipo Inscrito al torneo: {torneo.nombre}",
        context=context,
        template_name="emails/equipo_inscrito.html",
        to_emails=[torneo.organizador.email]
    )

def enviar_notificacion_torneo_aprobado(torneo):
    """
    Notifica al organizador (Dueño) que el administrador aprobó y publicó su torneo.
    """
    context = {
        'torneo': torneo,
        'organizador': torneo.organizador
    }
    enviar_email_base(
        subject=f"🎉 Tu Torneo ha sido Aprobado: {torneo.nombre}",
        context=context,
        template_name="emails/torneo_aprobado.html",
        to_emails=[torneo.organizador.email]
    )
