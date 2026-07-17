import os
from datetime import date

from fuentes.pendientes_cliente import cargar_tareas_pendientes, cargar_todas_las_tareas

RUTA_REPO_PENDIENTES_MOCK = os.path.join(os.path.dirname(__file__), "fixtures", "pendientes_mock")


def test_cargar_todas_las_tareas_lee_las_cuatro_tareas_del_fixture():
    tareas = cargar_todas_las_tareas(RUTA_REPO_PENDIENTES_MOCK)
    assert len(tareas) == 4


def test_cargar_todas_las_tareas_parsea_los_campos_correctamente():
    tareas = cargar_todas_las_tareas(RUTA_REPO_PENDIENTES_MOCK)
    tarea_grafos = next(tarea for tarea in tareas if tarea.titulo == "Taller 3 de grafos")

    assert tarea_grafos.curso == "algoritmos"
    assert tarea_grafos.fecha_limite == date(2026, 8, 10)
    assert tarea_grafos.energia_requerida == "alta"
    assert tarea_grafos.peso_academico == 15.0
    assert tarea_grafos.estado == "pendiente"


def test_cargar_tareas_pendientes_excluye_las_tareas_completadas():
    tareas_pendientes = cargar_tareas_pendientes(RUTA_REPO_PENDIENTES_MOCK)

    assert len(tareas_pendientes) == 3
    titulos = {tarea.titulo for tarea in tareas_pendientes}
    assert "Laboratorio 2 entregado" not in titulos


def test_cargar_tareas_pendientes_incluye_tareas_en_progreso():
    tareas_pendientes = cargar_tareas_pendientes(RUTA_REPO_PENDIENTES_MOCK)
    titulos = {tarea.titulo for tarea in tareas_pendientes}
    assert "Quiz de series" in titulos
