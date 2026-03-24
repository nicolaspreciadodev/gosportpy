from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Torneo, Equipo, Partido, PosicionEquipo

def inscribir_equipo_torneo(equipo: Equipo, torneo: Torneo) -> None:
    """
    Inscribe un equipo en un torneo, validando el límite máximo.
    """
    if torneo.equipos.count() >= torneo.max_equipos:
        raise ValidationError(f"El torneo ya alcanzó su límite de {torneo.max_equipos} equipos.")
    
    if torneo.equipos.filter(id=equipo.id).exists():
        raise ValidationError("El equipo ya está inscrito en este torneo.")
        
    torneo.equipos.add(equipo)

@transaction.atomic
def generar_fixture_liga(torneo: Torneo) -> bool:
    """
    Genera el fixture de liga (todos contra todos) usando el algoritmo Round-Robin.
    Inicializa la tabla de posiciones en 0.
    """
    if torneo.formato != 'LIGA':
        raise ValidationError("Solo se puede generar fixture para formato LIGA.")
        
    if torneo.fixture_generado:
        raise ValidationError("El fixture ya ha sido generado para este torneo.")
        
    equipos = list(torneo.equipos.all())
    num_equipos = len(equipos)
    
    if num_equipos < 2:
        raise ValidationError("Se necesitan al menos 2 equipos para generar el fixture.")
        
    # Si es impar, añadir un 'Dummy' (None) para los descansos
    if num_equipos % 2 != 0:
        equipos.append(None)
        num_equipos += 1
        
    total_jornadas = num_equipos - 1
    mitad = num_equipos // 2
    
    # Inicializar Tabla de Posiciones para los equipos (excluir Dummy)
    for equipo in [e for e in equipos if e is not None]:
        PosicionEquipo.objects.get_or_create(torneo=torneo, equipo=equipo)
    
    for jornada in range(total_jornadas):
        for i in range(mitad):
            equipo1 = equipos[i]
            equipo2 = equipos[num_equipos - 1 - i]
            
            # Si uno es None, el otro descansa esta jornada (no creamos partido)
            if equipo1 is not None and equipo2 is not None:
                # Alternar localía por cada jornada para ser justos en el round-robin (algoritmo genérico)
                if i % 2 == 1:
                    equipo_local, equipo_visitante = equipo2, equipo1
                else:
                    equipo_local, equipo_visitante = equipo1, equipo2
                    
                Partido.objects.create(
                    torneo=torneo,
                    equipo_local=equipo_local,
                    equipo_visitante=equipo_visitante,
                    jornada=jornada + 1,
                    estado='PENDIENTE'
                )
                
        # Rotar elementos para Round Robin (el primero se mantiene fijo)
        equipos.insert(1, equipos.pop())
        
    torneo.fixture_generado = True
    torneo.save()
    return True

@transaction.atomic
def registrar_resultado(partido: Partido, goles_l: int, goles_v: int, usuario) -> None:
    """
    Registra el resultado de un partido y dispara la actualización de posiciones.
    """
    if partido.torneo.organizador != usuario:
        raise ValidationError("Solo el organizador del torneo puede registrar resultados.")
        
    if partido.estado == 'JUGADO':
        raise ValidationError("Este partido ya cuenta con un resultado registrado.")
        
    partido.goles_local = goles_l
    partido.goles_visitante = goles_v
    partido.estado = 'JUGADO'
    partido.save()
    
    _actualizar_posiciones(partido.torneo)

def _actualizar_posiciones(torneo: Torneo) -> None:
    """
    Recalcula íntegramente la tabla de posiciones del torneo sumando 
    todos los partidos jugados. Es idempotente y resiliente a cambios manuales.
    """
    # 1. Resetear posiciones
    PosicionEquipo.objects.filter(torneo=torneo).update(
        puntos=0, partidos_jugados=0, partidos_ganados=0, 
        partidos_empatados=0, partidos_perdidos=0, 
        goles_favor=0, goles_contra=0
    )
    
    # 2. Recalcular
    posiciones = {pos.equipo.id: pos for pos in PosicionEquipo.objects.filter(torneo=torneo)}
    partidos_jugados = Partido.objects.filter(torneo=torneo, estado='JUGADO')
    
    for p in partidos_jugados:
        l_id = p.equipo_local.id
        v_id = p.equipo_visitante.id
        
        # Local stats
        pos_l = posiciones[l_id]
        pos_l.partidos_jugados += 1
        pos_l.goles_favor += p.goles_local
        pos_l.goles_contra += p.goles_visitante
        
        # Visitante stats
        pos_v = posiciones[v_id]
        pos_v.partidos_jugados += 1
        pos_v.goles_favor += p.goles_visitante
        pos_v.goles_contra += p.goles_local
        
        if p.goles_local > p.goles_visitante:
            pos_l.partidos_ganados += 1
            pos_l.puntos += 3
            pos_v.partidos_perdidos += 1
        elif p.goles_local < p.goles_visitante:
            pos_v.partidos_ganados += 1
            pos_v.puntos += 3
            pos_l.partidos_perdidos += 1
        else:
            pos_l.partidos_empatados += 1
            pos_l.puntos += 1
            pos_v.partidos_empatados += 1
            pos_v.puntos += 1
            
    # Guardar cambios batch
    PosicionEquipo.objects.bulk_update(
        posiciones.values(),
        ['puntos', 'partidos_jugados', 'partidos_ganados', 'partidos_empatados', 'partidos_perdidos', 'goles_favor', 'goles_contra']
    )
