from datetime import date, datetime, time

from modelo.bloque_fijo import BloqueFijo
from modelo.estado_fisiologico import EstadoFisiologico
from modelo.hueco_libre import HuecoLibre
from modelo.sesion_entrenamiento import SesionEntrenamiento
from modelo.tarea import Tarea
from motor.priorizador import AsignacionHueco, HorarioHoy, ResultadoPriorizacion
from motor.recomendador_entrenamiento import MANTENER, RecomendacionEntrenamiento
from salida.snapshot_diario import cargar_snapshot_diario, guardar_snapshot_diario

BLOQUE_MOVILES = BloqueFijo("miercoles", time(8, 0), time(9, 20), "clase", "moviles", "ISIS3510")

HORARIO_MIERCOLES = HorarioHoy(
    dia_semana="miercoles",
    bloques_fijos=[BLOQUE_MOVILES],
    huecos_libres=[HuecoLibre("miercoles", time(9, 20), time(14, 0))],
)

ESTADO_PRUEBA = EstadoFisiologico(
    momento=datetime(2026, 8, 5, 10, 0),
    training_readiness=70,
    training_status="productive",
    hrv_status="balanced",
    hrv_valor_ms=55.0,
    hrv_tendencia="estable",
    body_battery=60,
    acwr=1.1,
)

TAREA_PRUEBA = Tarea("algoritmos", "Taller 3 de grafos", date(2026, 8, 10), "alta", 15.0, "pendiente")
SESION_PRUEBA = SesionEntrenamiento(date(2026, 8, 5), "natacion", "alta", "Series de velocidad")
NOMBRES_CURSOS_PRUEBA = {"algoritmos": "Diseño de Algoritmos"}


def test_cargar_snapshot_diario_retorna_none_si_no_existe(tmp_path):
    assert cargar_snapshot_diario(str(tmp_path / "no_existe.json")) is None


def test_guardar_y_cargar_snapshot_diario_conserva_los_datos_principales(tmp_path):
    ruta_snapshot = tmp_path / "hoy_datos.json"
    asignaciones = [AsignacionHueco(HuecoLibre("miercoles", time(9, 20), time(14, 0)), TAREA_PRUEBA)]
    recomendacion = RecomendacionEntrenamiento(SESION_PRUEBA, MANTENER, "Se mantiene la sesion")
    resultado = ResultadoPriorizacion(None, asignaciones, recomendacion, ["una alerta de prueba"])

    guardar_snapshot_diario(
        str(ruta_snapshot), resultado, ESTADO_PRUEBA, HORARIO_MIERCOLES, NOMBRES_CURSOS_PRUEBA, date(2026, 8, 5)
    )
    snapshot = cargar_snapshot_diario(str(ruta_snapshot))

    assert snapshot["fecha"] == "2026-08-05"
    assert snapshot["dia_semana"] == "miercoles"
    assert snapshot["nombres_cursos"] == NOMBRES_CURSOS_PRUEBA
    assert snapshot["estado_fisiologico"]["body_battery"] == 60
    assert snapshot["resultado"]["alertas"] == ["una alerta de prueba"]
    assert snapshot["resultado"]["asignaciones"][0]["tarea"]["titulo"] == "Taller 3 de grafos"
    assert snapshot["resultado"]["recomendacion_entrenamiento"]["tipo_ajuste"] == MANTENER
    assert snapshot["bloques_fijos_hoy"][0]["nombre"] == "moviles"


def test_guardar_snapshot_diario_serializa_fechas_y_horas_como_texto(tmp_path):
    ruta_snapshot = tmp_path / "hoy_datos.json"
    resultado = ResultadoPriorizacion(None, [], None, [])

    guardar_snapshot_diario(
        str(ruta_snapshot), resultado, ESTADO_PRUEBA, HORARIO_MIERCOLES, NOMBRES_CURSOS_PRUEBA, date(2026, 8, 5)
    )
    snapshot = cargar_snapshot_diario(str(ruta_snapshot))

    assert snapshot["estado_fisiologico"]["momento"] == "2026-08-05T10:00:00"
    assert snapshot["bloques_fijos_hoy"][0]["hora_inicio"] == "08:00:00"


def test_guardar_snapshot_diario_con_estado_none(tmp_path):
    ruta_snapshot = tmp_path / "hoy_datos.json"
    resultado = ResultadoPriorizacion(None, [], None, ["Garmin no disponible"])

    guardar_snapshot_diario(str(ruta_snapshot), resultado, None, HORARIO_MIERCOLES, {}, date(2026, 8, 5))
    snapshot = cargar_snapshot_diario(str(ruta_snapshot))

    assert snapshot["estado_fisiologico"] is None


def test_guardar_snapshot_diario_con_bloque_fijo_activo(tmp_path):
    ruta_snapshot = tmp_path / "hoy_datos.json"
    resultado = ResultadoPriorizacion(BLOQUE_MOVILES, [], None, [])

    guardar_snapshot_diario(
        str(ruta_snapshot), resultado, ESTADO_PRUEBA, HORARIO_MIERCOLES, NOMBRES_CURSOS_PRUEBA, date(2026, 8, 5)
    )
    snapshot = cargar_snapshot_diario(str(ruta_snapshot))

    assert snapshot["resultado"]["bloque_fijo_activo"]["nombre"] == "moviles"
