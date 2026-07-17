import os
import shutil
from datetime import date

from fuentes.pendientes_cliente import (
    agregar_tarea,
    actualizar_estado_tarea,
    actualizar_tarea,
    cargar_tareas_pendientes,
    cargar_todas_las_tareas,
    eliminar_tarea,
    guardar_todas_las_tareas,
)
from modelo.tarea import Tarea

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


def _construir_repo_pendientes_de_prueba(tmp_path):
    ruta_repo_prueba = tmp_path / "pendientes_prueba"
    shutil.copytree(RUTA_REPO_PENDIENTES_MOCK, ruta_repo_prueba)
    return str(ruta_repo_prueba)


def test_guardar_todas_las_tareas_permite_releer_lo_mismo_que_se_guardo(tmp_path):
    ruta_repo_prueba = _construir_repo_pendientes_de_prueba(tmp_path)
    tareas_nuevas = [Tarea("web", "Tarea de prueba", date(2026, 9, 1), "media", 3.0, "pendiente")]

    guardar_todas_las_tareas(ruta_repo_prueba, tareas_nuevas)

    tareas_releidas = cargar_todas_las_tareas(ruta_repo_prueba)
    assert tareas_releidas == tareas_nuevas


def test_agregar_tarea_no_elimina_las_tareas_existentes(tmp_path):
    ruta_repo_prueba = _construir_repo_pendientes_de_prueba(tmp_path)
    cantidad_antes = len(cargar_todas_las_tareas(ruta_repo_prueba))
    tarea_nueva = Tarea("web", "Tarea agregada desde la interfaz", date(2026, 9, 5), "alta", 3.0, "pendiente")

    agregar_tarea(ruta_repo_prueba, tarea_nueva)

    tareas_despues = cargar_todas_las_tareas(ruta_repo_prueba)
    assert len(tareas_despues) == cantidad_antes + 1
    assert tareas_despues[-1] == tarea_nueva


def test_actualizar_estado_tarea_modifica_solo_la_tarea_indicada(tmp_path):
    ruta_repo_prueba = _construir_repo_pendientes_de_prueba(tmp_path)

    actualizar_estado_tarea(ruta_repo_prueba, 0, "completada")

    tareas = cargar_todas_las_tareas(ruta_repo_prueba)
    assert tareas[0].estado == "completada"
    assert tareas[1].estado != "completada"


def test_actualizar_tarea_reemplaza_todos_los_campos_de_la_tarea_indicada(tmp_path):
    ruta_repo_prueba = _construir_repo_pendientes_de_prueba(tmp_path)
    tarea_editada = Tarea("web", "Titulo editado", date(2026, 10, 1), "baja", 4.0, "en_progreso")

    actualizar_tarea(ruta_repo_prueba, 0, tarea_editada)

    tareas = cargar_todas_las_tareas(ruta_repo_prueba)
    assert tareas[0] == tarea_editada


def test_actualizar_tarea_no_afecta_las_demas_tareas(tmp_path):
    ruta_repo_prueba = _construir_repo_pendientes_de_prueba(tmp_path)
    tareas_antes = cargar_todas_las_tareas(ruta_repo_prueba)
    tarea_editada = Tarea("web", "Titulo editado", date(2026, 10, 1), "baja", 4.0, "en_progreso")

    actualizar_tarea(ruta_repo_prueba, 0, tarea_editada)

    tareas_despues = cargar_todas_las_tareas(ruta_repo_prueba)
    assert tareas_despues[1:] == tareas_antes[1:]


def test_eliminar_tarea_remueve_solo_la_tarea_indicada(tmp_path):
    ruta_repo_prueba = _construir_repo_pendientes_de_prueba(tmp_path)
    tareas_antes = cargar_todas_las_tareas(ruta_repo_prueba)
    titulo_eliminado = tareas_antes[0].titulo

    eliminar_tarea(ruta_repo_prueba, 0)

    tareas_despues = cargar_todas_las_tareas(ruta_repo_prueba)
    assert len(tareas_despues) == len(tareas_antes) - 1
    assert titulo_eliminado not in {tarea.titulo for tarea in tareas_despues}
