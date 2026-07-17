import os
from datetime import datetime, time

import pytest

from fuentes.horario_cliente import (
    bloque_fijo_activo,
    calcular_huecos_libres,
    cargar_bloques_fijos,
    nombre_dia_semana,
)

RUTA_CONFIG_MOCK = os.path.join(os.path.dirname(__file__), "fixtures", "config_mock.yaml")


@pytest.fixture
def bloques_fijos_prueba():
    return cargar_bloques_fijos(RUTA_CONFIG_MOCK)


def test_cargar_bloques_fijos_lee_los_tres_bloques_del_fixture(bloques_fijos_prueba):
    assert len(bloques_fijos_prueba) == 3
    assert bloques_fijos_prueba[0].nombre == "natacion"
    assert bloques_fijos_prueba[0].hora_inicio == time(6, 0)
    assert bloques_fijos_prueba[0].hora_fin == time(7, 50)


def test_nombre_dia_semana_identifica_lunes_correctamente():
    momento = datetime(2026, 8, 3, 10, 0)
    assert nombre_dia_semana(momento) == "lunes"


def test_bloque_fijo_activo_durante_entrenamiento_matutino(bloques_fijos_prueba):
    momento = datetime(2026, 8, 3, 6, 30)
    bloque = bloque_fijo_activo(momento, bloques_fijos_prueba)
    assert bloque is not None
    assert bloque.nombre == "natacion"


def test_bloque_fijo_activo_en_borde_de_inicio_incluye_el_bloque(bloques_fijos_prueba):
    momento = datetime(2026, 8, 3, 6, 0)
    bloque = bloque_fijo_activo(momento, bloques_fijos_prueba)
    assert bloque is not None
    assert bloque.nombre == "natacion"


def test_bloque_fijo_activo_en_borde_de_fin_ya_no_incluye_el_bloque(bloques_fijos_prueba):
    momento = datetime(2026, 8, 3, 7, 50)
    bloque = bloque_fijo_activo(momento, bloques_fijos_prueba)
    assert bloque is None


def test_bloque_fijo_activo_fuera_de_cualquier_bloque_retorna_none(bloques_fijos_prueba):
    momento = datetime(2026, 8, 3, 10, 0)
    assert bloque_fijo_activo(momento, bloques_fijos_prueba) is None


def test_bloque_fijo_activo_mismo_horario_otro_dia_no_aplica(bloques_fijos_prueba):
    momento = datetime(2026, 8, 5, 6, 30)
    assert bloque_fijo_activo(momento, bloques_fijos_prueba) is None


def test_calcular_huecos_libres_lunes_devuelve_huecos_entre_y_despues_de_bloques(bloques_fijos_prueba):
    huecos = calcular_huecos_libres("lunes", bloques_fijos_prueba)

    assert len(huecos) == 3
    assert huecos[0].hora_inicio == time(0, 0)
    assert huecos[0].hora_fin == time(6, 0)
    assert huecos[1].hora_inicio == time(7, 50)
    assert huecos[1].hora_fin == time(8, 0)
    assert huecos[2].hora_inicio == time(9, 20)
    assert huecos[2].hora_fin == time(23, 59)


def test_calcular_huecos_libres_dia_sin_bloques_devuelve_el_dia_completo(bloques_fijos_prueba):
    huecos = calcular_huecos_libres("miercoles", bloques_fijos_prueba)

    assert len(huecos) == 1
    assert huecos[0].hora_inicio == time(0, 0)
    assert huecos[0].hora_fin == time(23, 59)


def test_calcular_huecos_libres_martes_deja_hueco_antes_y_despues_del_unico_bloque(bloques_fijos_prueba):
    huecos = calcular_huecos_libres("martes", bloques_fijos_prueba)

    assert len(huecos) == 2
    assert huecos[0].hora_inicio == time(0, 0)
    assert huecos[0].hora_fin == time(14, 0)
    assert huecos[1].hora_inicio == time(15, 20)
    assert huecos[1].hora_fin == time(23, 59)
