from datetime import datetime

from modelo.estado_fisiologico import EstadoFisiologico
from motor.agente_entrenamiento import (
    OBJETIVO_RECUPERACION,
    OBJETIVO_RESISTENCIA,
    OBJETIVO_TECNICA,
    OBJETIVO_VELOCIDAD,
    sugerir_parametros_sesion,
)


def _estado(training_status="productive", body_battery=70, acwr=1.0):
    return EstadoFisiologico(
        momento=datetime(2026, 8, 3, 8, 0),
        training_readiness=70,
        training_status=training_status,
        hrv_status="balanced",
        hrv_valor_ms=60.0,
        hrv_tendencia=None,
        body_battery=body_battery,
        acwr=acwr,
    )


def test_sin_estado_fisiologico_sugiere_resistencia_por_defecto():
    sugerencia = sugerir_parametros_sesion(None)
    assert sugerencia.objetivo == OBJETIVO_RESISTENCIA


def test_estado_de_sobreentrenamiento_sugiere_recuperacion():
    sugerencia = sugerir_parametros_sesion(_estado(training_status="overreaching"))
    assert sugerencia.objetivo == OBJETIVO_RECUPERACION


def test_acwr_alto_sugiere_recuperacion():
    sugerencia = sugerir_parametros_sesion(_estado(acwr=2.0), acwr_limite=1.5)
    assert sugerencia.objetivo == OBJETIVO_RECUPERACION


def test_estado_de_sobreentrenamiento_tiene_prioridad_sobre_acwr():
    sugerencia = sugerir_parametros_sesion(_estado(training_status="detraining", acwr=0.5), acwr_limite=1.5)
    assert sugerencia.objetivo == OBJETIVO_RECUPERACION
    assert "detraining" in sugerencia.justificacion


def test_body_battery_bajo_sugiere_tecnica():
    sugerencia = sugerir_parametros_sesion(_estado(body_battery=30), body_battery_bajo=40)
    assert sugerencia.objetivo == OBJETIVO_TECNICA


def test_body_battery_medio_sugiere_resistencia():
    sugerencia = sugerir_parametros_sesion(_estado(body_battery=55), body_battery_bajo=40, body_battery_medio=70)
    assert sugerencia.objetivo == OBJETIVO_RESISTENCIA


def test_body_battery_alto_sugiere_velocidad():
    sugerencia = sugerir_parametros_sesion(_estado(body_battery=85), body_battery_bajo=40, body_battery_medio=70)
    assert sugerencia.objetivo == OBJETIVO_VELOCIDAD


def test_acwr_none_no_bloquea_la_evaluacion_por_body_battery():
    estado = _estado(body_battery=85, acwr=None)
    sugerencia = sugerir_parametros_sesion(estado, body_battery_bajo=40, body_battery_medio=70)
    assert sugerencia.objetivo == OBJETIVO_VELOCIDAD


def test_todas_las_sugerencias_incluyen_al_menos_un_estilo():
    sugerencia = sugerir_parametros_sesion(_estado())
    assert len(sugerencia.estilos) >= 1
