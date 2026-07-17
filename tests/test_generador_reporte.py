from datetime import date, datetime, time

from modelo.bloque_fijo import BloqueFijo
from modelo.estado_fisiologico import EstadoFisiologico
from modelo.hueco_libre import HuecoLibre
from modelo.sesion_entrenamiento import SesionEntrenamiento
from modelo.tarea import Tarea
from motor.priorizador import AsignacionHueco, HorarioHoy, ResultadoPriorizacion
from motor.recomendador_entrenamiento import RECUPERACION_ACTIVA, RecomendacionEntrenamiento
from salida.generador_reporte import generar_contenido_reporte, generar_reporte

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


def test_generar_contenido_reporte_con_bloque_fijo_activo_omite_estado_fisiologico():
    resultado = ResultadoPriorizacion(BLOQUE_MOVILES, [], None, [])
    contenido = generar_contenido_reporte(resultado, ESTADO_PRUEBA, HORARIO_MIERCOLES)

    assert "Ahora mismo" in contenido
    assert "moviles" in contenido
    assert "Estado fisiologico" not in contenido


def test_generar_contenido_reporte_incluye_alertas_cuando_hay_alguna():
    resultado = ResultadoPriorizacion(None, [], None, ["HRV desbalanceado con body battery bajo"])
    contenido = generar_contenido_reporte(resultado, ESTADO_PRUEBA, HORARIO_MIERCOLES)

    assert "Alertas" in contenido
    assert "HRV desbalanceado con body battery bajo" in contenido


def test_generar_contenido_reporte_omite_alertas_cuando_no_hay_ninguna():
    resultado = ResultadoPriorizacion(None, [], None, [])
    contenido = generar_contenido_reporte(resultado, ESTADO_PRUEBA, HORARIO_MIERCOLES)

    assert "Alertas" not in contenido


def test_generar_contenido_reporte_lista_tareas_asignadas_por_hueco():
    asignaciones = [AsignacionHueco(HuecoLibre("miercoles", time(9, 20), time(14, 0)), TAREA_PRUEBA)]
    resultado = ResultadoPriorizacion(None, asignaciones, None, [])
    contenido = generar_contenido_reporte(resultado, ESTADO_PRUEBA, HORARIO_MIERCOLES)

    assert "09:20-14:00" in contenido
    assert "Taller 3 de grafos" in contenido


def test_generar_contenido_reporte_incluye_recomendacion_de_entrenamiento():
    recomendacion = RecomendacionEntrenamiento(SESION_PRUEBA, RECUPERACION_ACTIVA, "Se reemplaza por recuperacion activa")
    resultado = ResultadoPriorizacion(None, [], recomendacion, [])
    contenido = generar_contenido_reporte(resultado, ESTADO_PRUEBA, HORARIO_MIERCOLES)

    assert RECUPERACION_ACTIVA in contenido
    assert "Se reemplaza por recuperacion activa" in contenido


def test_generar_contenido_reporte_usa_nombre_completo_del_curso_cuando_hay_mapeo():
    asignaciones = [AsignacionHueco(HuecoLibre("miercoles", time(9, 20), time(14, 0)), TAREA_PRUEBA)]
    resultado = ResultadoPriorizacion(None, asignaciones, None, [])
    nombres_cursos = {"algoritmos": "Diseño de Algoritmos"}

    contenido = generar_contenido_reporte(resultado, ESTADO_PRUEBA, HORARIO_MIERCOLES, nombres_cursos)

    assert "Diseño de Algoritmos" in contenido


def test_generar_contenido_reporte_usa_el_slug_si_no_hay_mapeo_de_nombres():
    resultado = ResultadoPriorizacion(BLOQUE_MOVILES, [], None, [])
    contenido = generar_contenido_reporte(resultado, ESTADO_PRUEBA, HORARIO_MIERCOLES)

    assert "moviles" in contenido


def test_generar_reporte_escribe_el_archivo_en_disco(tmp_path):
    resultado = ResultadoPriorizacion(None, [], None, [])
    ruta_salida = tmp_path / "hoy.md"

    ruta_devuelta = generar_reporte(resultado, ESTADO_PRUEBA, HORARIO_MIERCOLES, ruta_salida=str(ruta_salida))

    assert ruta_devuelta == str(ruta_salida)
    assert ruta_salida.exists()
    assert "Reporte del dia" in ruta_salida.read_text(encoding="utf-8")
