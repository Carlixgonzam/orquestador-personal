import os
import shutil
from datetime import date, time
from unittest.mock import MagicMock

import pytest
import requests

import interfaz.app as modulo_interfaz
from fuentes.entrenamiento_cliente import cargar_plan_semana_actual, nombre_archivo_plan_semana_actual
from fuentes.pendientes_cliente import cargar_todas_las_tareas, guardar_todas_las_tareas
from interfaz.vista_semanal import calcular_lunes_de_la_semana
from modelo.bloque_fijo import BloqueFijo

RUTA_REPO_PENDIENTES_MOCK = os.path.join(os.path.dirname(__file__), "fixtures", "pendientes_mock")
RUTA_REPO_NOTAS_ALGORITMOS_MOCK = os.path.join(os.path.dirname(__file__), "fixtures", "notas_mock", "notas-algoritmos")
RUTA_HISTORIAL_MOCK = os.path.join(os.path.dirname(__file__), "fixtures", "historial_mock.csv")
NOMBRES_CURSOS_PRUEBA = {"algoritmos": "Diseño de Algoritmos", "web": "Programación Web"}

SNAPSHOT_PRUEBA = {
    "fecha": "2026-08-05",
    "dia_semana": "miercoles",
    "nombres_cursos": NOMBRES_CURSOS_PRUEBA,
    "bloques_fijos_hoy": [],
    "resultado": {
        "bloque_fijo_activo": None,
        "asignaciones": [
            {
                "hueco": {"dia_semana": "miercoles", "hora_inicio": "09:20:00", "hora_fin": "14:00:00"},
                "tarea": {
                    "curso": "algoritmos",
                    "titulo": "Tarea del snapshot de prueba",
                    "fecha_limite": "2026-08-10",
                    "energia_requerida": "alta",
                    "peso_academico": 3.0,
                    "estado": "pendiente",
                },
            }
        ],
        "recomendacion_entrenamiento": {
            "sesion_planeada": None,
            "tipo_ajuste": "sin_sesion_planeada",
            "justificacion": "No hay sesion de entrenamiento planeada para hoy",
        },
        "alertas": [],
    },
    "estado_fisiologico": {
        "momento": "2026-08-05T10:00:00",
        "training_readiness": 70,
        "training_status": "productive",
        "hrv_status": "balanced",
        "hrv_valor_ms": 55.0,
        "hrv_tendencia": "estable",
        "body_battery": 60,
        "eventos_body_battery": [],
        "vo2_max": None,
        "endurance_score": None,
        "predicciones_carrera": {},
        "frecuencia_cardiaca_reposo": 48,
        "frecuencia_respiratoria": 14.5,
        "estres_promedio": 30,
        "acwr": 1.1,
    },
}


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
    monkeypatch.setattr(modulo_interfaz, "_cargar_snapshot_hoy", lambda: SNAPSHOT_PRUEBA)
    monkeypatch.setattr(
        modulo_interfaz,
        "_bloques_fijos_por_dia_de_la_semana",
        lambda lunes: {"miercoles": [BloqueFijo("miercoles", time(8, 0), time(9, 20), "clase", "algoritmos", "ISIS2112")]},
    )
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
    assert "Tarea del snapshot de prueba" in cuerpo


def test_index_muestra_el_dashboard_con_stats_del_snapshot(cliente_de_prueba):
    cliente, _, _ = cliente_de_prueba
    cuerpo = cliente.get("/").get_data(as_text=True)

    assert "cuadricula-stats" in cuerpo
    assert "60" in cuerpo
    assert "Body battery" in cuerpo
    assert "<pre>" not in cuerpo


def test_index_sin_snapshot_muestra_mensaje_de_bienvenida(cliente_de_prueba, monkeypatch):
    cliente, _, _ = cliente_de_prueba
    monkeypatch.setattr(modulo_interfaz, "_cargar_snapshot_hoy", lambda: None)

    cuerpo = cliente.get("/").get_data(as_text=True)

    assert "Aun no se ha generado ningun reporte" in cuerpo


def test_index_con_bloque_fijo_activo_muestra_el_banner_y_omite_las_tarjetas(cliente_de_prueba, monkeypatch):
    cliente, _, _ = cliente_de_prueba
    snapshot_con_bloque_activo = dict(SNAPSHOT_PRUEBA)
    snapshot_con_bloque_activo["resultado"] = dict(SNAPSHOT_PRUEBA["resultado"])
    snapshot_con_bloque_activo["resultado"]["bloque_fijo_activo"] = {
        "dia_semana": "miercoles",
        "hora_inicio": "08:00:00",
        "hora_fin": "09:20:00",
        "tipo": "clase",
        "nombre": "algoritmos",
        "codigo": "ISIS2112",
    }
    monkeypatch.setattr(modulo_interfaz, "_cargar_snapshot_hoy", lambda: snapshot_con_bloque_activo)

    cuerpo = cliente.get("/").get_data(as_text=True)

    assert "banner-bloque-activo" in cuerpo
    assert "cuadricula-stats" not in cuerpo


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


def test_semana_muestra_los_siete_dias(cliente_de_prueba):
    cliente, _, _ = cliente_de_prueba
    cuerpo = cliente.get("/semana").get_data(as_text=True)

    assert cuerpo.count("dia-columna-header") == 7
    assert "Lunes" in cuerpo
    assert "Domingo" in cuerpo


def test_semana_muestra_el_bloque_fijo_del_dia_correcto(cliente_de_prueba):
    cliente, _, _ = cliente_de_prueba
    cuerpo = cliente.get("/semana").get_data(as_text=True)

    assert "Diseño de Algoritmos" in cuerpo


def test_semana_muestra_la_sesion_de_entrenamiento_de_hoy(cliente_de_prueba):
    cliente, _, _ = cliente_de_prueba
    cuerpo = cliente.get("/semana").get_data(as_text=True)

    assert "Natacion" in cuerpo


def test_semana_muestra_la_tarea_en_el_dia_de_su_deadline(cliente_de_prueba):
    cliente, ruta_repo_pendientes, _ = cliente_de_prueba
    lunes = calcular_lunes_de_la_semana(date.today())
    tareas = cargar_todas_las_tareas(ruta_repo_pendientes)
    primera_tarea = tareas[0]
    primera_tarea.fecha_limite = lunes
    guardar_todas_las_tareas(ruta_repo_pendientes, tareas)

    cuerpo = cliente.get("/semana").get_data(as_text=True)

    assert primera_tarea.titulo in cuerpo


def test_generar_sesion_desde_dsl_agrega_la_sesion_generada(cliente_de_prueba, monkeypatch):
    cliente, _, ruta_repo_entrenamiento = cliente_de_prueba
    cantidad_antes = len(cargar_plan_semana_actual(ruta_repo_entrenamiento))
    cliente_dsl_falso = MagicMock()
    cliente_dsl_falso.generar_sesion.return_value = {
        "success": True,
        "code": "session Entreno1 {\n  warmup 400 freestyle\n}",
        "goal": "endurance",
        "distance": 2000,
    }
    monkeypatch.setattr(modulo_interfaz, "ClienteSwimmingDSL", lambda: cliente_dsl_falso)

    respuesta = cliente.post(
        "/entrenamiento/generar-dsl",
        data={
            "fecha": date.today().isoformat(),
            "objetivo": "endurance",
            "distancia": "2000",
            "duracion": "60",
            "estilos": ["freestyle"],
        },
    )

    assert respuesta.status_code == 302
    cliente_dsl_falso.generar_sesion.assert_called_once_with(
        objetivo="endurance", distancia=2000, estilos=["freestyle"], duracion=60
    )
    sesiones = cargar_plan_semana_actual(ruta_repo_entrenamiento)
    assert len(sesiones) == cantidad_antes + 1
    assert "warmup 400 freestyle" in sesiones[-1].notas


def test_generar_sesion_desde_dsl_sin_servidor_muestra_mensaje_flash(cliente_de_prueba, monkeypatch):
    cliente, _, _ = cliente_de_prueba
    cliente_dsl_falso = MagicMock()
    cliente_dsl_falso.generar_sesion.side_effect = requests.exceptions.ConnectionError()
    monkeypatch.setattr(modulo_interfaz, "ClienteSwimmingDSL", lambda: cliente_dsl_falso)

    respuesta = cliente.post(
        "/entrenamiento/generar-dsl",
        data={
            "fecha": date.today().isoformat(),
            "objetivo": "endurance",
            "distancia": "2000",
            "duracion": "60",
            "estilos": ["freestyle"],
        },
        follow_redirects=True,
    )

    assert respuesta.status_code == 200
    assert "servidor de swimmingdsl" in respuesta.get_data(as_text=True)
