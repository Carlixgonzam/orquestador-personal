import os

from fuentes.cursos_cliente import cargar_nombres_cursos

RUTA_CONFIG_REAL = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
RUTA_CONFIG_MOCK = os.path.join(os.path.dirname(__file__), "fixtures", "config_mock.yaml")


def test_cargar_nombres_cursos_lee_el_mapeo_del_config_real():
    nombres_cursos = cargar_nombres_cursos(RUTA_CONFIG_REAL)

    assert nombres_cursos["algoritmos"] == "Diseño de Algoritmos"
    assert nombres_cursos["concurrencia"] == "Concurrencia, Paralelismo y Distribución"


def test_cargar_nombres_cursos_retorna_vacio_si_no_existe_la_clave():
    nombres_cursos = cargar_nombres_cursos(RUTA_CONFIG_MOCK)
    assert nombres_cursos == {}
