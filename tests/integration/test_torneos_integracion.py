"""
Pruebas de Integración - Flujo de Torneos y Gestión de Ligas.

Verifica la inscripción de equipos, la generación transaccional del fixture
(Round-Robin) y la actualización relacional de la tabla de posiciones.
"""
import pytest
import datetime
from django.urls import reverse
from usuarios.models import CustomUser
from negocio.models import Torneo, Equipo, Partido, PosicionEquipo

@pytest.mark.django_db
class TestFlujoTorneosIntegracion:
    """Pruebas End-to-End para el ciclo de vida de un Torneo (Liga)."""

    @pytest.fixture
    def setup_torneo(self):
        """Prepara un torneo y múltiples equipos en BD."""
        organizador = CustomUser.objects.create_user(
            username='org_torneos',
            email='org@test.com',
            password='Password123*',
            rol='DEPORTISTA'
        )
        # Se requiere is_approved=True para generar fixture
        torneo = Torneo.objects.create(
            nombre='Liga Premier Bogotá',
            descripcion='Torneo de prueba integración',
            organizador=organizador,
            fecha_inicio=datetime.date(2026, 7, 1),
            fecha_fin=datetime.date(2026, 8, 1),
            max_equipos=4,
            formato='LIGA',
            estado='PUBLICADO',
            is_approved=True,
            precio_inscripcion=100000.00
        )
        
        equipos = []
        for i in range(4):
            equipo = Equipo.objects.create(nombre=f'Equipo {i+1}')
            equipos.append(equipo)
            
        return {
            'torneo': torneo,
            'organizador': organizador,
            'equipos': equipos
        }

    def test_flujo_completo_torneo_liga(self, app_cliente, setup_torneo):
        """
        # Arrange
        Cargamos el torneo y los equipos preparados.
        Autenticamos al cliente como el organizador del torneo para tener permisos.
        """
        torneo = setup_torneo['torneo']
        organizador = setup_torneo['organizador']
        equipos = setup_torneo['equipos']
        
        app_cliente.force_login(organizador)

        """
        # Act 1 - Inscripción de Equipos
        Usamos la lógica de negocio para inscribir a los 4 equipos al torneo.
        """
        from negocio.services import inscribir_equipo_torneo
        for eq in equipos:
            inscribir_equipo_torneo(eq, torneo)

        # Assert 1
        assert torneo.equipos.count() == 4
        
        """
        # Act 2 - Generación de Fixture HTTP POST
        Llamamos al endpoint para generar el fixture. Esto ejecutará el 
        algoritmo Round-Robin real y creará las posiciones.
        """
        url_generar = reverse('negocio:generar_fixture', kwargs={'pk': torneo.id})
        respuesta_fixture = app_cliente.post(url_generar)

        # Assert 2
        assert respuesta_fixture.status_code == 302 # Redirección exitosa
        torneo.refresh_from_db()
        assert torneo.fixture_generado is True
        
        # 4 equipos generan 6 partidos en total en Round-Robin
        partidos = Partido.objects.filter(torneo=torneo)
        assert partidos.count() == 6
        
        # Se deben haber creado las 4 filas en la tabla de posiciones inicializada
        posiciones = PosicionEquipo.objects.filter(torneo=torneo)
        assert posiciones.count() == 4

        """
        # Act 3 - Registro de Resultado HTTP POST
        Simulamos el envío de un resultado para el primer partido.
        """
        partido_a_jugar = partidos.first()
        url_resultado = reverse('negocio:registrar_resultado', kwargs={'pk': partido_a_jugar.id})
        
        # Enviamos 3 - 1 a favor del local
        respuesta_resultado = app_cliente.post(url_resultado, {
            'goles_local': 3,
            'goles_visitante': 1
        })
        
        # Assert 3
        assert respuesta_resultado.status_code == 302
        partido_a_jugar.refresh_from_db()
        assert partido_a_jugar.estado == 'JUGADO'
        assert partido_a_jugar.goles_local == 3
        assert partido_a_jugar.goles_visitante == 1
        
        """
        # Act 4 / Assert Final - Verificación de Posiciones
        Revisamos la tabla relacional transaccional. El equipo local debe
        tener 3 puntos y +2 en diferencia de goles. El visitante 0 puntos y -2.
        """
        pos_local = PosicionEquipo.objects.get(torneo=torneo, equipo=partido_a_jugar.equipo_local)
        pos_visitante = PosicionEquipo.objects.get(torneo=torneo, equipo=partido_a_jugar.equipo_visitante)
        
        assert pos_local.puntos == 3
        assert pos_local.partidos_ganados == 1
        assert pos_local.goles_favor == 3
        assert pos_local.goles_contra == 1
        assert pos_local.diferencia_goles == 2
        
        assert pos_visitante.puntos == 0
        assert pos_visitante.partidos_perdidos == 1
        assert pos_visitante.goles_favor == 1
        assert pos_visitante.goles_contra == 3
        assert pos_visitante.diferencia_goles == -2
