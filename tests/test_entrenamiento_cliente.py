import os
from datetime import date

from fuentes.entrenamiento_cliente import (
    cargar_plan_semana_actual,
    nombre_archivo_plan_semana_actual,
    obtener_sesion_de_hoy,
)

RUTA_REPO_ENTRENAMIENTO_MOCK = os.path.join(os.path.dirname(__file__), "fixtures", "entrenamiento_mock")
FECHA_PRUEBA = date(2026, 8, 3)


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
