import os
import shutil
from datetime import date

import pytest

import interfaz.app as modulo_interfaz
from fuentes.entrenamiento_cliente import cargar_plan_semana_actual, nombre_archivo_plan_semana_actual
from fuentes.pendientes_cliente import cargar_todas_las_tareas

RUTA_REPO_PENDIENTES_MOCK = os.path.join(os.path.dirname(__file__), "fixtures", "pendientes_mock")
RUTA_REPO_NOTAS_ALGORITMOS_MOCK = os.path.join(os.path.dirname(__file__), "fixtures", "notas_mock", "notas-algoritmos")
RUTA_HISTORIAL_MOCK = os.path.join(os.path.dirname(__file__), "fixtures", "historial_mock.csv")
NOMBRES_CURSOS_PRUEBA = {"algoritmos": "Diseño de Algoritmos", "web": "Programación Web"}


def _construir_repo_entrenamiento_de_prueba(tmp_path):
    ruta_repo_prueba = tmp_path / "entrenamiento_prueba"
    ruta_repo_prueba.mkdir()
    nombre_archivo = nombre_archivo_plan_semana_actual()
    contenido = (
        "sesiones:\n"
        f'  - fecha: "{date.today().isoformat()}"\n'
        "    tipo: natacion\n"
        "    intensidad: alta\n"
        '    notas: "Sesion de prueba"\n'
    )
    (ruta_repo_prueba / nombre_archivo).write_text(contenido, encoding="utf-8")
    return str(ruta_repo_prueba)


@pytest.fixture
def cliente_de_prueba(tmp_path, monkeypatch):
    ruta_repo_prueba = tmp_path / "pendientes_prueba"
    shutil.copytree(RUTA_REPO_PENDIENTES_MOCK, ruta_repo_prueba)
    ruta_repo_entrenamiento_prueba = _construir_repo_entrenamiento_de_prueba(tmp_path)
    monkeypatch.setattr(modulo_interfaz, "_ruta_repo_pendientes", lambda: str(ruta_repo_prueba))
    monkeypatch.setattr(modulo_interfaz, "_ruta_repo_entrenamiento", lambda: ruta_repo_entrenamiento_prueba)
    monkeypatch.setattr(modulo_interfaz, "_leer_contenido_hoy", lambda: "reporte de prueba")
    monkeypatch.setattr(modulo_interfaz, "_nombres_cursos", lambda: NOMBRES_CURSOS_PRUEBA)
    monkeypatch.setattr(modulo_interfaz, "RUTA_HISTORIAL_POR_DEFECTO", RUTA_HISTORIAL_MOCK)
    monkeypatch.setattr(
        modulo_interfaz,
        "_repos_notas",
        lambda: [{"nombre": "notas-algoritmos", "ruta_local": RUTA_REPO_NOTAS_ALGORITMOS_MOCK}],
    )
    modulo_interfaz.app.config["TESTING"] = True
    return modulo_interfaz.app.test_client(), str(ruta_repo_prueba), ruta_repo_entrenamiento_prueba


def test_index_muestra_las_tareas_existentes(cliente_de_prueba):
    cliente, _, _ = cliente_de_prueba
    respuesta = cliente.get("/")

    assert respuesta.status_code == 200
    cuerpo = respuesta.get_data(as_text=True)
    assert "Taller 3 de grafos" in cuerpo
    assert "reporte de prueba" in cuerpo


def test_index_muestra_hallazgos_de_notas_para_el_curso_de_la_tarea(cliente_de_prueba):
    cliente, _, _ = cliente_de_prueba
    respuesta = cliente.get("/")

    cuerpo = respuesta.get_data(as_text=True)
    assert "Dijkstra no funciona con pesos negativos" in cuerpo
    assert "Cae complejidad de Floyd-Warshall" in cuerpo


def test_crear_tarea_la_agrega_al_repo(cliente_de_prueba):
    cliente, ruta_repo_prueba, _ = cliente_de_prueba
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
    cliente, ruta_repo_prueba, _ = cliente_de_prueba

    respuesta = cliente.post("/tareas/0/completar")

    assert respuesta.status_code == 302
    tareas = cargar_todas_las_tareas(ruta_repo_prueba)
    assert tareas[0].estado == "completada"


def test_eliminar_tarea_la_remueve_del_repo(cliente_de_prueba):
    cliente, ruta_repo_prueba, _ = cliente_de_prueba
    cantidad_antes = len(cargar_todas_las_tareas(ruta_repo_prueba))

    respuesta = cliente.post("/tareas/0/eliminar")

    assert respuesta.status_code == 302
    tareas = cargar_todas_las_tareas(ruta_repo_prueba)
    assert len(tareas) == cantidad_antes - 1


def test_index_muestra_el_nombre_completo_del_curso(cliente_de_prueba):
    cliente, _, _ = cliente_de_prueba
    cuerpo = cliente.get("/").get_data(as_text=True)

    assert "Diseño de Algoritmos" in cuerpo


def test_formulario_editar_tarea_precarga_los_valores_actuales(cliente_de_prueba):
    cliente, _, _ = cliente_de_prueba
    cuerpo = cliente.get("/tareas/0/editar").get_data(as_text=True)

    assert "Taller 3 de grafos" in cuerpo
    assert 'value="2026-08-10"' in cuerpo


def test_guardar_edicion_tarea_actualiza_los_campos(cliente_de_prueba):
    cliente, ruta_repo_prueba, _ = cliente_de_prueba

    respuesta = cliente.post(
        "/tareas/0/editar",
        data={
            "curso": "web",
            "titulo": "Taller 3 de grafos (editado)",
            "fecha_limite": "2026-08-15",
            "energia_requerida": "media",
            "peso_academico": "4",
            "estado": "en_progreso",
        },
    )

    assert respuesta.status_code == 302
    tareas = cargar_todas_las_tareas(ruta_repo_prueba)
    assert tareas[0].titulo == "Taller 3 de grafos (editado)"
    assert tareas[0].curso == "web"
    assert tareas[0].estado == "en_progreso"


def test_rendimiento_muestra_graficas_y_tabla_con_historial(cliente_de_prueba):
    cliente, _, _ = cliente_de_prueba
    respuesta = cliente.get("/rendimiento")

    assert respuesta.status_code == 200
    cuerpo = respuesta.get_data(as_text=True)
    assert "<svg" in cuerpo
    assert "2026-07-17" in cuerpo
    assert "OVERREACHING" in cuerpo


def test_rendimiento_sin_historial_muestra_mensaje(cliente_de_prueba, tmp_path, monkeypatch):
    cliente, _, _ = cliente_de_prueba
    monkeypatch.setattr(modulo_interfaz, "RUTA_HISTORIAL_POR_DEFECTO", str(tmp_path / "no_existe.csv"))

    cuerpo = cliente.get("/rendimiento").get_data(as_text=True)

    assert "Todavia no hay historial" in cuerpo


def test_entrenamiento_muestra_las_sesiones_de_la_semana_actual(cliente_de_prueba):
    cliente, _, _ = cliente_de_prueba
    cuerpo = cliente.get("/entrenamiento").get_data(as_text=True)

    assert "Sesion de prueba" in cuerpo
    assert "natacion" in cuerpo


def test_crear_sesion_la_agrega_al_plan_de_la_semana(cliente_de_prueba):
    cliente, _, ruta_repo_entrenamiento = cliente_de_prueba
    cantidad_antes = len(cargar_plan_semana_actual(ruta_repo_entrenamiento))

    respuesta = cliente.post(
        "/entrenamiento",
        data={
            "fecha": date.today().isoformat(),
            "tipo": "ciclismo",
            "intensidad": "baja",
            "notas": "Sesion creada desde la interfaz",
        },
    )

    assert respuesta.status_code == 302
    sesiones = cargar_plan_semana_actual(ruta_repo_entrenamiento)
    assert len(sesiones) == cantidad_antes + 1
    assert sesiones[-1].notas == "Sesion creada desde la interfaz"


def test_formulario_editar_sesion_precarga_los_valores_actuales(cliente_de_prueba):
    cliente, _, _ = cliente_de_prueba
    cuerpo = cliente.get("/entrenamiento/0/editar").get_data(as_text=True)

    assert "Sesion de prueba" in cuerpo


def test_guardar_edicion_sesion_actualiza_los_campos(cliente_de_prueba):
    cliente, _, ruta_repo_entrenamiento = cliente_de_prueba

    respuesta = cliente.post(
        "/entrenamiento/0/editar",
        data={
            "fecha": date.today().isoformat(),
            "tipo": "running",
            "intensidad": "moderada",
            "notas": "Sesion editada",
        },
    )

    assert respuesta.status_code == 302
    sesiones = cargar_plan_semana_actual(ruta_repo_entrenamiento)
    assert sesiones[0].tipo == "running"
    assert sesiones[0].notas == "Sesion editada"


def test_eliminar_sesion_la_remueve_del_plan(cliente_de_prueba):
    cliente, _, ruta_repo_entrenamiento = cliente_de_prueba
    cantidad_antes = len(cargar_plan_semana_actual(ruta_repo_entrenamiento))

    respuesta = cliente.post("/entrenamiento/0/eliminar")

    assert respuesta.status_code == 302
    sesiones = cargar_plan_semana_actual(ruta_repo_entrenamiento)
    assert len(sesiones) == cantidad_antes - 1
