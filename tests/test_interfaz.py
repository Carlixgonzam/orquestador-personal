import os
import shutil

import pytest

import interfaz.app as modulo_interfaz
from fuentes.pendientes_cliente import cargar_todas_las_tareas

RUTA_REPO_PENDIENTES_MOCK = os.path.join(os.path.dirname(__file__), "fixtures", "pendientes_mock")
RUTA_REPO_NOTAS_ALGORITMOS_MOCK = os.path.join(os.path.dirname(__file__), "fixtures", "notas_mock", "notas-algoritmos")
RUTA_HISTORIAL_MOCK = os.path.join(os.path.dirname(__file__), "fixtures", "historial_mock.csv")
NOMBRES_CURSOS_PRUEBA = {"algoritmos": "Diseño de Algoritmos", "web": "Programación Web"}


@pytest.fixture
def cliente_de_prueba(tmp_path, monkeypatch):
    ruta_repo_prueba = tmp_path / "pendientes_prueba"
    shutil.copytree(RUTA_REPO_PENDIENTES_MOCK, ruta_repo_prueba)
    monkeypatch.setattr(modulo_interfaz, "_ruta_repo_pendientes", lambda: str(ruta_repo_prueba))
    monkeypatch.setattr(modulo_interfaz, "_leer_contenido_hoy", lambda: "reporte de prueba")
    monkeypatch.setattr(modulo_interfaz, "_nombres_cursos", lambda: NOMBRES_CURSOS_PRUEBA)
    monkeypatch.setattr(modulo_interfaz, "RUTA_HISTORIAL_POR_DEFECTO", RUTA_HISTORIAL_MOCK)
    monkeypatch.setattr(
        modulo_interfaz,
        "_repos_notas",
        lambda: [{"nombre": "notas-algoritmos", "ruta_local": RUTA_REPO_NOTAS_ALGORITMOS_MOCK}],
    )
    modulo_interfaz.app.config["TESTING"] = True
    return modulo_interfaz.app.test_client(), str(ruta_repo_prueba)


def test_index_muestra_las_tareas_existentes(cliente_de_prueba):
    cliente, _ = cliente_de_prueba
    respuesta = cliente.get("/")

    assert respuesta.status_code == 200
    cuerpo = respuesta.get_data(as_text=True)
    assert "Taller 3 de grafos" in cuerpo
    assert "reporte de prueba" in cuerpo


def test_index_muestra_hallazgos_de_notas_para_el_curso_de_la_tarea(cliente_de_prueba):
    cliente, _ = cliente_de_prueba
    respuesta = cliente.get("/")

    cuerpo = respuesta.get_data(as_text=True)
    assert "Dijkstra no funciona con pesos negativos" in cuerpo
    assert "Cae complejidad de Floyd-Warshall" in cuerpo


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


def test_index_muestra_el_nombre_completo_del_curso(cliente_de_prueba):
    cliente, _ = cliente_de_prueba
    cuerpo = cliente.get("/").get_data(as_text=True)

    assert "Diseño de Algoritmos" in cuerpo


def test_rendimiento_muestra_graficas_y_tabla_con_historial(cliente_de_prueba):
    cliente, _ = cliente_de_prueba
    respuesta = cliente.get("/rendimiento")

    assert respuesta.status_code == 200
    cuerpo = respuesta.get_data(as_text=True)
    assert "<svg" in cuerpo
    assert "2026-07-17" in cuerpo
    assert "OVERREACHING" in cuerpo


def test_rendimiento_sin_historial_muestra_mensaje(cliente_de_prueba, tmp_path, monkeypatch):
    cliente, _ = cliente_de_prueba
    monkeypatch.setattr(modulo_interfaz, "RUTA_HISTORIAL_POR_DEFECTO", str(tmp_path / "no_existe.csv"))

    cuerpo = cliente.get("/rendimiento").get_data(as_text=True)

    assert "Todavia no hay historial" in cuerpo
