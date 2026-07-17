import os
import shutil
from datetime import date

from fuentes.entrenamiento_cliente import (
    agregar_sesion,
    actualizar_sesion,
    cargar_plan_semana_actual,
    eliminar_sesion,
    nombre_archivo_plan_semana_actual,
    obtener_sesion_de_hoy,
)
from modelo.sesion_entrenamiento import SesionEntrenamiento

RUTA_REPO_ENTRENAMIENTO_MOCK = os.path.join(os.path.dirname(__file__), "fixtures", "entrenamiento_mock")
FECHA_PRUEBA = date(2026, 8, 3)


def _construir_repo_entrenamiento_de_prueba(tmp_path):
    ruta_repo_prueba = tmp_path / "entrenamiento_prueba"
    shutil.copytree(RUTA_REPO_ENTRENAMIENTO_MOCK, ruta_repo_prueba)
    return str(ruta_repo_prueba)


def test_nombre_archivo_plan_semana_actual_usa_la_semana_iso():
    assert nombre_archivo_plan_semana_actual(FECHA_PRUEBA) == "plan-semana-32.yaml"


def test_cargar_plan_semana_actual_lee_las_tres_sesiones_del_fixture():
    sesiones = cargar_plan_semana_actual(RUTA_REPO_ENTRENAMIENTO_MOCK, FECHA_PRUEBA)
    assert len(sesiones) == 3


def test_cargar_plan_semana_actual_parsea_los_campos_correctamente():
    sesiones = cargar_plan_semana_actual(RUTA_REPO_ENTRENAMIENTO_MOCK, FECHA_PRUEBA)
    sesion_lunes = sesiones[0]

    assert sesion_lunes.fecha == date(2026, 8, 3)
    assert sesion_lunes.tipo == "natacion"
    assert sesion_lunes.intensidad == "moderada"
    assert sesion_lunes.notas == "Series de resistencia aerobica"


def test_obtener_sesion_de_hoy_encuentra_la_sesion_correspondiente():
    sesiones = cargar_plan_semana_actual(RUTA_REPO_ENTRENAMIENTO_MOCK, FECHA_PRUEBA)
    sesion_de_hoy = obtener_sesion_de_hoy(sesiones, FECHA_PRUEBA)

    assert sesion_de_hoy is not None
    assert sesion_de_hoy.intensidad == "moderada"


def test_obtener_sesion_de_hoy_retorna_none_si_no_hay_sesion_planeada():
    sesiones = cargar_plan_semana_actual(RUTA_REPO_ENTRENAMIENTO_MOCK, FECHA_PRUEBA)
    fecha_sin_sesion = date(2026, 8, 5)

    assert obtener_sesion_de_hoy(sesiones, fecha_sin_sesion) is None


def test_cargar_plan_semana_actual_retorna_vacio_si_la_semana_no_tiene_archivo():
    sesiones = cargar_plan_semana_actual(RUTA_REPO_ENTRENAMIENTO_MOCK, date(2026, 1, 5))
    assert sesiones == []


def test_agregar_sesion_la_agrega_al_archivo_de_su_semana(tmp_path):
    ruta_repo_prueba = _construir_repo_entrenamiento_de_prueba(tmp_path)
    cantidad_antes = len(cargar_plan_semana_actual(ruta_repo_prueba, FECHA_PRUEBA))
    sesion_nueva = SesionEntrenamiento(FECHA_PRUEBA, "ciclismo", "baja", "Sesion agregada desde la interfaz")

    agregar_sesion(ruta_repo_prueba, sesion_nueva)

    sesiones = cargar_plan_semana_actual(ruta_repo_prueba, FECHA_PRUEBA)
    assert len(sesiones) == cantidad_antes + 1
    assert sesiones[-1] == sesion_nueva


def test_agregar_sesion_en_semana_sin_archivo_lo_crea(tmp_path):
    ruta_repo_prueba = _construir_repo_entrenamiento_de_prueba(tmp_path)
    fecha_semana_nueva = date(2026, 1, 5)
    sesion_nueva = SesionEntrenamiento(fecha_semana_nueva, "running", "moderada", "Primera sesion de la semana")

    agregar_sesion(ruta_repo_prueba, sesion_nueva)

    sesiones = cargar_plan_semana_actual(ruta_repo_prueba, fecha_semana_nueva)
    assert sesiones == [sesion_nueva]


def test_actualizar_sesion_reemplaza_solo_la_sesion_indicada(tmp_path):
    ruta_repo_prueba = _construir_repo_entrenamiento_de_prueba(tmp_path)
    sesion_editada = SesionEntrenamiento(FECHA_PRUEBA, "natacion", "alta", "Editada")

    actualizar_sesion(ruta_repo_prueba, FECHA_PRUEBA, 0, sesion_editada)

    sesiones = cargar_plan_semana_actual(ruta_repo_prueba, FECHA_PRUEBA)
    assert sesiones[0] == sesion_editada


def test_eliminar_sesion_remueve_solo_la_sesion_indicada(tmp_path):
    ruta_repo_prueba = _construir_repo_entrenamiento_de_prueba(tmp_path)
    cantidad_antes = len(cargar_plan_semana_actual(ruta_repo_prueba, FECHA_PRUEBA))

    eliminar_sesion(ruta_repo_prueba, FECHA_PRUEBA, 0)

    sesiones = cargar_plan_semana_actual(ruta_repo_prueba, FECHA_PRUEBA)
    assert len(sesiones) == cantidad_antes - 1
