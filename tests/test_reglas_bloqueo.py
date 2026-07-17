from datetime import datetime

import pytest

from fuentes.horario_cliente import cargar_bloques_fijos
from modelo.estado_fisiologico import EstadoFisiologico
from motor.reglas_bloqueo import (
    es_ventana_entrenamiento_matutino,
    hay_acwr_alto,
    hay_bloque_fijo_activo,
    hay_hrv_desbalanceado_con_bateria_baja,
    hay_sobreentrenamiento,
)

import os

RUTA_CONFIG_MOCK = os.path.join(os.path.dirname(__file__), "fixtures", "config_mock.yaml")


@pytest.fixture
def bloques_fijos_prueba():
    return cargar_bloques_fijos(RUTA_CONFIG_MOCK)


def construir_estado_fisiologico(
    momento=None,
    training_readiness=70,
    training_status="productive",
    hrv_status="balanced",
    body_battery=60,
    acwr=1.0,
):
    return EstadoFisiologico(
        momento=momento or datetime(2026, 8, 3, 12, 0),
        training_readiness=training_readiness,
        training_status=training_status,
        hrv_status=hrv_status,
        hrv_valor_ms=55.0,
        hrv_tendencia="estable",
        body_battery=body_battery,
        acwr=acwr,
    )


def test_hay_bloque_fijo_activo_retorna_el_bloque_durante_una_clase(bloques_fijos_prueba):
    momento = datetime(2026, 8, 3, 8, 30)
    bloque = hay_bloque_fijo_activo(momento, bloques_fijos_prueba)
    assert bloque is not None
    assert bloque.nombre == "moviles"


def test_hay_bloque_fijo_activo_retorna_none_en_hueco_libre(bloques_fijos_prueba):
    momento = datetime(2026, 8, 3, 10, 0)
    assert hay_bloque_fijo_activo(momento, bloques_fijos_prueba) is None


@pytest.mark.parametrize("estado", ["overreaching", "detraining", "Overreaching", "DETRAINING"])
def test_hay_sobreentrenamiento_detecta_estados_criticos(estado):
    estado_fisiologico = construir_estado_fisiologico(training_status=estado)
    assert hay_sobreentrenamiento(estado_fisiologico) is True


@pytest.mark.parametrize("estado", ["productive", "maintaining", "recovery"])
def test_hay_sobreentrenamiento_false_para_estados_no_criticos(estado):
    estado_fisiologico = construir_estado_fisiologico(training_status=estado)
    assert hay_sobreentrenamiento(estado_fisiologico) is False


def test_hay_acwr_alto_true_cuando_supera_el_limite():
    estado_fisiologico = construir_estado_fisiologico(acwr=1.8)
    assert hay_acwr_alto(estado_fisiologico, acwr_limite=1.5) is True


def test_hay_acwr_alto_false_cuando_esta_justo_en_el_limite():
    estado_fisiologico = construir_estado_fisiologico(acwr=1.5)
    assert hay_acwr_alto(estado_fisiologico, acwr_limite=1.5) is False


def test_hay_acwr_alto_false_cuando_acwr_no_esta_disponible():
    estado_fisiologico = construir_estado_fisiologico(acwr=None)
    assert hay_acwr_alto(estado_fisiologico, acwr_limite=1.5) is False


def test_es_ventana_entrenamiento_matutino_true_lunes_antes_de_las_nueve():
    momento = datetime(2026, 8, 3, 7, 0)
    assert es_ventana_entrenamiento_matutino(momento) is True


def test_es_ventana_entrenamiento_matutino_false_lunes_despues_de_las_nueve():
    momento = datetime(2026, 8, 3, 9, 30)
    assert es_ventana_entrenamiento_matutino(momento) is False


def test_es_ventana_entrenamiento_matutino_false_en_miercoles():
    momento = datetime(2026, 8, 5, 7, 0)
    assert es_ventana_entrenamiento_matutino(momento) is False


def test_hay_hrv_desbalanceado_con_bateria_baja_true_fuera_de_ventana_matutina():
    estado_fisiologico = construir_estado_fisiologico(hrv_status="unbalanced", body_battery=30)
    momento = datetime(2026, 8, 3, 12, 0)
    assert hay_hrv_desbalanceado_con_bateria_baja(estado_fisiologico, momento, body_battery_bajo=40) is True


def test_hay_hrv_desbalanceado_con_bateria_baja_false_si_bateria_no_es_baja():
    estado_fisiologico = construir_estado_fisiologico(hrv_status="unbalanced", body_battery=80)
    momento = datetime(2026, 8, 3, 12, 0)
    assert hay_hrv_desbalanceado_con_bateria_baja(estado_fisiologico, momento, body_battery_bajo=40) is False


def test_hay_hrv_desbalanceado_con_bateria_baja_false_si_hrv_esta_balanceado():
    estado_fisiologico = construir_estado_fisiologico(hrv_status="balanced", body_battery=30)
    momento = datetime(2026, 8, 3, 12, 0)
    assert hay_hrv_desbalanceado_con_bateria_baja(estado_fisiologico, momento, body_battery_bajo=40) is False


def test_hay_hrv_desbalanceado_con_bateria_baja_false_durante_ventana_entrenamiento_matutino():
    estado_fisiologico = construir_estado_fisiologico(hrv_status="unbalanced", body_battery=20)
    momento = datetime(2026, 8, 3, 6, 30)
    assert hay_hrv_desbalanceado_con_bateria_baja(estado_fisiologico, momento, body_battery_bajo=40) is False
