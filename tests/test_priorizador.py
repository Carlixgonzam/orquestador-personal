from datetime import date, datetime, time

from modelo.bloque_fijo import BloqueFijo
from modelo.estado_fisiologico import EstadoFisiologico
from modelo.hueco_libre import HuecoLibre
from modelo.sesion_entrenamiento import SesionEntrenamiento
from modelo.tarea import Tarea
from motor.priorizador import HorarioHoy, decidir_hoy, decidir_hoy_sin_garmin
from motor.recomendador_entrenamiento import MANTENER, RECUPERACION_ACTIVA, REDUCIR_INTENSIDAD

BLOQUE_MOVILES = BloqueFijo("miercoles", time(8, 0), time(9, 20), "clase", "moviles", "ISIS3510")
BLOQUE_NATACION_LUNES = BloqueFijo("lunes", time(6, 0), time(7, 50), "entrenamiento", "natacion")

HORARIO_MIERCOLES = HorarioHoy(
    dia_semana="miercoles",
    bloques_fijos=[BLOQUE_MOVILES],
    huecos_libres=[
        HuecoLibre("miercoles", time(9, 20), time(14, 0)),
        HuecoLibre("miercoles", time(15, 20), time(23, 59)),
    ],
)

HORARIO_LUNES_MATUTINO = HorarioHoy(
    dia_semana="lunes",
    bloques_fijos=[BLOQUE_NATACION_LUNES],
    huecos_libres=[HuecoLibre("lunes", time(7, 50), time(23, 59))],
)

SESION_PLANEADA = SesionEntrenamiento(date(2026, 8, 5), "natacion", "alta", "Series de velocidad")


def construir_tarea(curso="algoritmos", titulo="tarea", fecha_limite=date(2026, 8, 10), energia_requerida="alta", peso_academico=10.0):
    return Tarea(curso, titulo, fecha_limite, energia_requerida, peso_academico, "pendiente")


def construir_estado(
    momento=datetime(2026, 8, 5, 10, 0),
    training_readiness=70,
    training_status="productive",
    hrv_status="balanced",
    body_battery=60,
    acwr=1.0,
):
    return EstadoFisiologico(
        momento=momento,
        training_readiness=training_readiness,
        training_status=training_status,
        hrv_status=hrv_status,
        hrv_valor_ms=55.0,
        hrv_tendencia="estable",
        body_battery=body_battery,
        acwr=acwr,
    )


TAREAS_MIXTAS = [
    construir_tarea(titulo="alta_lejana", energia_requerida="alta", fecha_limite=date(2026, 8, 20), peso_academico=5),
    construir_tarea(titulo="alta_cercana", energia_requerida="alta", fecha_limite=date(2026, 8, 6), peso_academico=10),
    construir_tarea(titulo="media_unica", energia_requerida="media", fecha_limite=date(2026, 8, 8), peso_academico=8),
    construir_tarea(titulo="baja_peso_bajo", energia_requerida="baja", fecha_limite=date(2026, 8, 7), peso_academico=3),
    construir_tarea(titulo="baja_peso_alto", energia_requerida="baja", fecha_limite=date(2026, 8, 7), peso_academico=12),
]


def test_regla_1_bloque_fijo_activo_no_genera_recomendaciones():
    estado = construir_estado(momento=datetime(2026, 8, 3, 6, 30))
    resultado = decidir_hoy(estado, TAREAS_MIXTAS, HORARIO_LUNES_MATUTINO)

    assert resultado.bloque_fijo_activo is not None
    assert resultado.bloque_fijo_activo.nombre == "natacion"
    assert resultado.asignaciones == []
    assert resultado.recomendacion_entrenamiento is None
    assert resultado.alertas == []


def test_regla_2_sobreentrenamiento_solo_asigna_tareas_de_baja_energia():
    estado = construir_estado(training_status="overreaching")
    resultado = decidir_hoy(estado, TAREAS_MIXTAS, HORARIO_MIERCOLES, sesion_planeada_hoy=SESION_PLANEADA)

    tareas_asignadas = [asignacion.tarea for asignacion in resultado.asignaciones if asignacion.tarea]
    assert all(tarea.energia_requerida == "baja" for tarea in tareas_asignadas)
    assert resultado.alertas != []
    assert resultado.recomendacion_entrenamiento.tipo_ajuste == RECUPERACION_ACTIVA


def test_regla_2_ordena_las_tareas_de_baja_energia_por_deadline_y_peso():
    estado = construir_estado(training_status="detraining")
    resultado = decidir_hoy(estado, TAREAS_MIXTAS, HORARIO_MIERCOLES, sesion_planeada_hoy=SESION_PLANEADA)

    primera_tarea = resultado.asignaciones[0].tarea
    assert primera_tarea.titulo == "baja_peso_alto"


def test_regla_3_acwr_alto_prioriza_academico_sin_filtrar_por_energia():
    estado = construir_estado(acwr=1.8)
    resultado = decidir_hoy(estado, TAREAS_MIXTAS, HORARIO_MIERCOLES, sesion_planeada_hoy=SESION_PLANEADA, acwr_limite=1.5)

    tareas_asignadas = [asignacion.tarea for asignacion in resultado.asignaciones if asignacion.tarea]
    niveles_energia = {tarea.energia_requerida for tarea in tareas_asignadas}
    assert len(niveles_energia) > 1
    assert resultado.recomendacion_entrenamiento.tipo_ajuste == REDUCIR_INTENSIDAD
    assert resultado.alertas != []


def test_regla_4_hrv_desbalanceado_con_bateria_baja_solo_tareas_administrativas():
    estado = construir_estado(hrv_status="unbalanced", body_battery=25)
    resultado = decidir_hoy(estado, TAREAS_MIXTAS, HORARIO_MIERCOLES, body_battery_bajo=40)

    tareas_asignadas = [asignacion.tarea for asignacion in resultado.asignaciones if asignacion.tarea]
    assert all(tarea.energia_requerida == "baja" for tarea in tareas_asignadas)
    assert resultado.alertas != []


def test_regla_4_no_aplica_durante_ventana_de_entrenamiento_matutino():
    estado = construir_estado(momento=datetime(2026, 8, 3, 8, 30), hrv_status="unbalanced", body_battery=25)
    resultado = decidir_hoy(estado, TAREAS_MIXTAS, HORARIO_LUNES_MATUTINO, body_battery_bajo=40)

    assert resultado.alertas == []


def test_regla_5_matching_fino_body_battery_alto():
    estado = construir_estado(body_battery=90)
    resultado = decidir_hoy(estado, TAREAS_MIXTAS, HORARIO_MIERCOLES, body_battery_bajo=40, body_battery_medio=70)

    tareas_asignadas = [asignacion.tarea for asignacion in resultado.asignaciones if asignacion.tarea]
    assert all(tarea.energia_requerida == "alta" for tarea in tareas_asignadas)
    assert resultado.alertas == []
    assert tareas_asignadas[0].titulo == "alta_cercana"


def test_regla_5_matching_fino_body_battery_medio():
    estado = construir_estado(body_battery=55)
    resultado = decidir_hoy(estado, TAREAS_MIXTAS, HORARIO_MIERCOLES, body_battery_bajo=40, body_battery_medio=70)

    tareas_asignadas = [asignacion.tarea for asignacion in resultado.asignaciones if asignacion.tarea]
    assert all(tarea.energia_requerida == "media" for tarea in tareas_asignadas)


def test_regla_5_matching_fino_body_battery_bajo():
    estado = construir_estado(body_battery=20, hrv_status="balanced")
    resultado = decidir_hoy(estado, TAREAS_MIXTAS, HORARIO_MIERCOLES, body_battery_bajo=40, body_battery_medio=70)

    tareas_asignadas = [asignacion.tarea for asignacion in resultado.asignaciones if asignacion.tarea]
    assert all(tarea.energia_requerida == "baja" for tarea in tareas_asignadas)
    assert resultado.alertas == []


def test_regla_5_recomendacion_entrenamiento_mantiene_la_sesion():
    estado = construir_estado(body_battery=90, training_status="productive", acwr=1.0)
    resultado = decidir_hoy(estado, TAREAS_MIXTAS, HORARIO_MIERCOLES, sesion_planeada_hoy=SESION_PLANEADA)

    assert resultado.recomendacion_entrenamiento.tipo_ajuste == MANTENER


def test_reparte_una_tarea_por_hueco_libre_y_deja_huecos_sin_tarea_si_faltan():
    estado = construir_estado(body_battery=90)
    tareas_una_sola = [construir_tarea(titulo="unica", energia_requerida="alta")]
    resultado = decidir_hoy(estado, tareas_una_sola, HORARIO_MIERCOLES)

    assert len(resultado.asignaciones) == 2
    assert resultado.asignaciones[0].tarea.titulo == "unica"
    assert resultado.asignaciones[1].tarea is None


def test_prioridad_regla_2_sobre_regla_3_cuando_ambas_aplican():
    estado = construir_estado(training_status="overreaching", acwr=2.0)
    resultado = decidir_hoy(estado, TAREAS_MIXTAS, HORARIO_MIERCOLES, sesion_planeada_hoy=SESION_PLANEADA, acwr_limite=1.5)

    tareas_asignadas = [asignacion.tarea for asignacion in resultado.asignaciones if asignacion.tarea]
    assert all(tarea.energia_requerida == "baja" for tarea in tareas_asignadas)
    assert resultado.recomendacion_entrenamiento.tipo_ajuste == RECUPERACION_ACTIVA


def test_decidir_hoy_sin_garmin_respeta_bloque_fijo_activo():
    momento = datetime(2026, 8, 3, 6, 30)
    resultado = decidir_hoy_sin_garmin(TAREAS_MIXTAS, HORARIO_LUNES_MATUTINO, momento)

    assert resultado.bloque_fijo_activo is not None
    assert resultado.bloque_fijo_activo.nombre == "natacion"
    assert resultado.asignaciones == []
    assert resultado.alertas == []


def test_decidir_hoy_sin_garmin_asigna_todas_las_tareas_sin_filtrar_por_energia():
    momento = datetime(2026, 8, 5, 10, 0)
    resultado = decidir_hoy_sin_garmin(TAREAS_MIXTAS, HORARIO_MIERCOLES, momento)

    tareas_asignadas = [asignacion.tarea for asignacion in resultado.asignaciones if asignacion.tarea]
    niveles_energia = {tarea.energia_requerida for tarea in tareas_asignadas}
    assert len(niveles_energia) > 1
    assert resultado.alertas != []


def test_decidir_hoy_sin_garmin_ordena_por_deadline_y_peso():
    momento = datetime(2026, 8, 5, 10, 0)
    resultado = decidir_hoy_sin_garmin(TAREAS_MIXTAS, HORARIO_MIERCOLES, momento)

    assert resultado.asignaciones[0].tarea.titulo == "alta_cercana"


def test_decidir_hoy_sin_garmin_mantiene_la_sesion_planeada_por_defecto():
    momento = datetime(2026, 8, 5, 10, 0)
    resultado = decidir_hoy_sin_garmin(TAREAS_MIXTAS, HORARIO_MIERCOLES, momento, sesion_planeada_hoy=SESION_PLANEADA)

    assert resultado.recomendacion_entrenamiento.tipo_ajuste == MANTENER
    assert resultado.recomendacion_entrenamiento.sesion_planeada == SESION_PLANEADA
