from datetime import date, time

from interfaz.vista_semanal import calcular_lunes_de_la_semana, construir_vista_semanal
from modelo.bloque_fijo import BloqueFijo
from modelo.sesion_entrenamiento import SesionEntrenamiento
from modelo.tarea import Tarea


def test_calcular_lunes_de_la_semana_desde_un_miercoles():
    assert calcular_lunes_de_la_semana(date(2026, 8, 5)) == date(2026, 8, 3)


def test_calcular_lunes_de_la_semana_desde_un_lunes():
    assert calcular_lunes_de_la_semana(date(2026, 8, 3)) == date(2026, 8, 3)


def test_calcular_lunes_de_la_semana_desde_un_domingo():
    assert calcular_lunes_de_la_semana(date(2026, 8, 9)) == date(2026, 8, 3)


def test_construir_vista_semanal_genera_siete_dias_en_orden():
    dias = construir_vista_semanal(date(2026, 8, 3), {}, [], [])

    assert len(dias) == 7
    assert [dia["dia_semana"] for dia in dias] == [
        "lunes",
        "martes",
        "miercoles",
        "jueves",
        "viernes",
        "sabado",
        "domingo",
    ]
    assert dias[0]["fecha"] == date(2026, 8, 3)
    assert dias[6]["fecha"] == date(2026, 8, 9)


def test_construir_vista_semanal_asigna_bloques_fijos_al_dia_correcto():
    bloque_moviles = BloqueFijo("miercoles", time(8, 0), time(9, 20), "clase", "moviles", "ISIS3510")
    dias = construir_vista_semanal(date(2026, 8, 3), {"miercoles": [bloque_moviles]}, [], [])

    dia_miercoles = next(dia for dia in dias if dia["dia_semana"] == "miercoles")
    dia_lunes = next(dia for dia in dias if dia["dia_semana"] == "lunes")
    assert dia_miercoles["bloques_fijos"] == [bloque_moviles]
    assert dia_lunes["bloques_fijos"] == []


def test_construir_vista_semanal_asigna_la_sesion_de_entrenamiento_del_dia():
    sesion_martes = SesionEntrenamiento(date(2026, 8, 4), "natacion", "alta", "Series")
    dias = construir_vista_semanal(date(2026, 8, 3), {}, [sesion_martes], [])

    dia_martes = next(dia for dia in dias if dia["dia_semana"] == "martes")
    dia_lunes = next(dia for dia in dias if dia["dia_semana"] == "lunes")
    assert dia_martes["sesion_entrenamiento"] == sesion_martes
    assert dia_lunes["sesion_entrenamiento"] is None


def test_construir_vista_semanal_agrupa_tareas_por_fecha_limite():
    tarea_jueves = Tarea("algoritmos", "Taller", date(2026, 8, 6), "alta", 3.0, "pendiente")
    tarea_otra_semana = Tarea("web", "Quiz", date(2026, 8, 20), "media", 3.0, "pendiente")
    dias = construir_vista_semanal(date(2026, 8, 3), {}, [], [tarea_jueves, tarea_otra_semana])

    dia_jueves = next(dia for dia in dias if dia["dia_semana"] == "jueves")
    dia_viernes = next(dia for dia in dias if dia["dia_semana"] == "viernes")
    assert dia_jueves["tareas_del_dia"] == [tarea_jueves]
    assert dia_viernes["tareas_del_dia"] == []
