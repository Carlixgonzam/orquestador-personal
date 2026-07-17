import os
import shutil

import pytest

import interfaz.app as modulo_interfaz
from fuentes.pendientes_cliente import cargar_todas_las_tareas

RUTA_REPO_PENDIENTES_MOCK = os.path.join(os.path.dirname(__file__), "fixtures", "pendientes_mock")


@pytest.fixture
def cliente_de_prueba(tmp_path, monkeypatch):
    ruta_repo_prueba = tmp_path / "pendientes_prueba"
    shutil.copytree(RUTA_REPO_PENDIENTES_MOCK, ruta_repo_prueba)
    monkeypatch.setattr(modulo_interfaz, "_ruta_repo_pendientes", lambda: str(ruta_repo_prueba))
    monkeypatch.setattr(modulo_interfaz, "_leer_contenido_hoy", lambda: "reporte de prueba")
    modulo_interfaz.app.config["TESTING"] = True
    return modulo_interfaz.app.test_client(), str(ruta_repo_prueba)


def test_index_muestra_las_tareas_existentes(cliente_de_prueba):
    cliente, _ = cliente_de_prueba
    respuesta = cliente.get("/")

    assert respuesta.status_code == 200
    cuerpo = respuesta.get_data(as_text=True)
    assert "Taller 3 de grafos" in cuerpo
    assert "reporte de prueba" in cuerpo


def test_crear_tarea_la_agrega_al_repo(cliente_de_prueba):
    cliente, ruta_repo_prueba = cliente_de_prueba
    cantidad_antes = len(cargar_todas_las_tareas(ruta_repo_prueba))

    respuesta = cliente.post(
        "/tareas",
        data={
            "curso": "web",
            "titulo": "Tarea creada desde la interfaz",
            "fecha_limite": "2026-09-01",
            "energia_requerida": "media",
            "peso_academico": "3",
        },
    )

    assert respuesta.status_code == 302
    tareas = cargar_todas_las_tareas(ruta_repo_prueba)
    assert len(tareas) == cantidad_antes + 1
    assert tareas[-1].titulo == "Tarea creada desde la interfaz"
    assert tareas[-1].estado == "pendiente"


def test_completar_tarea_cambia_su_estado(cliente_de_prueba):
    cliente, ruta_repo_prueba = cliente_de_prueba

    respuesta = cliente.post("/tareas/0/completar")

    assert respuesta.status_code == 302
    tareas = cargar_todas_las_tareas(ruta_repo_prueba)
    assert tareas[0].estado == "completada"


def test_eliminar_tarea_la_remueve_del_repo(cliente_de_prueba):
    cliente, ruta_repo_prueba = cliente_de_prueba
    cantidad_antes = len(cargar_todas_las_tareas(ruta_repo_prueba))

    respuesta = cliente.post("/tareas/0/eliminar")

    assert respuesta.status_code == 302
    tareas = cargar_todas_las_tareas(ruta_repo_prueba)
    assert len(tareas) == cantidad_antes - 1
