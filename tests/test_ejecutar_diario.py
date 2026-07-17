import json
import os
from datetime import date, time
from unittest.mock import MagicMock

import pytest
import yaml

from scripts.ejecutar_diario import (
    _extraer_nivel_body_battery,
    construir_estado_fisiologico,
    construir_horario_hoy,
    ejecutar,
)

RUTA_GARMIN_MOCK = os.path.join(os.path.dirname(__file__), "fixtures", "garmin_mock.json")
RUTA_CONFIG_MOCK = os.path.join(os.path.dirname(__file__), "fixtures", "config_mock.yaml")
RUTA_PENDIENTES_MOCK = os.path.join(os.path.dirname(__file__), "fixtures", "pendientes_mock")
RUTA_ENTRENAMIENTO_MOCK = os.path.join(os.path.dirname(__file__), "fixtures", "entrenamiento_mock")
FECHA_PRUEBA = date(2026, 8, 5)


@pytest.fixture
def datos_garmin_mock():
    with open(RUTA_GARMIN_MOCK, encoding="utf-8") as archivo:
        return json.load(archivo)


@pytest.fixture
def cliente_garmin_falso(datos_garmin_mock):
    cliente = MagicMock()
    cliente.obtener_disposicion_entrenamiento.return_value = datos_garmin_mock["training_readiness"]
    cliente.obtener_hrv.return_value = datos_garmin_mock["hrv_data"]
    cliente.obtener_estado_entrenamiento.return_value = datos_garmin_mock["training_status"]
    cliente.obtener_metricas_maximas.return_value = datos_garmin_mock["max_metrics"]
    cliente.obtener_score_resistencia.return_value = datos_garmin_mock["endurance_score"]
    cliente.obtener_predicciones_carrera.return_value = datos_garmin_mock["race_predictions"]
    cliente.obtener_frecuencia_cardiaca_reposo.return_value = datos_garmin_mock["rhr_day"]
    cliente.obtener_frecuencia_respiratoria.return_value = datos_garmin_mock["respiration_data"]
    cliente.obtener_estres.return_value = datos_garmin_mock["stress_data"]
    cliente.obtener_eventos_body_battery.return_value = datos_garmin_mock["body_battery_events"]
    cliente.obtener_nivel_body_battery.return_value = datos_garmin_mock["body_battery"]
    return cliente


def _construir_ruta_config_de_prueba(tmp_path):
    with open(RUTA_CONFIG_MOCK, encoding="utf-8") as archivo:
        configuracion = yaml.safe_load(archivo)
    configuracion["rutas_repos"] = {
        "pendientes": RUTA_PENDIENTES_MOCK,
        "entrenamiento": RUTA_ENTRENAMIENTO_MOCK,
    }
    ruta_config_prueba = tmp_path / "config.yaml"
    with open(ruta_config_prueba, "w", encoding="utf-8") as archivo:
        yaml.safe_dump(configuracion, archivo)
    return str(ruta_config_prueba)


def test_construir_estado_fisiologico_extrae_los_campos_esperados(cliente_garmin_falso):
    estado = construir_estado_fisiologico(cliente_garmin_falso, FECHA_PRUEBA)

    assert estado.training_readiness == 78
    assert estado.training_status == "PRODUCTIVE"
    assert estado.hrv_status == "BALANCED"
    assert estado.hrv_valor_ms == 55
    assert estado.body_battery == 45
    assert estado.acwr == pytest.approx(1.18)
    assert estado.vo2_max == 48.5
    assert estado.endurance_score == 62
    assert estado.frecuencia_cardiaca_reposo == 48
    assert estado.frecuencia_respiratoria == 14.5
    assert estado.estres_promedio == 32
    assert estado.momento.date() == FECHA_PRUEBA


def test_extraer_nivel_body_battery_toma_el_ultimo_valor_del_dia():
    datos_body_battery = [{"charged": 60, "bodyBatteryValuesArray": [[1754200000000, 75], [1754201000000, 45]]}]
    assert _extraer_nivel_body_battery(datos_body_battery) == 45


def test_extraer_nivel_body_battery_usa_charged_si_no_hay_valores_del_dia():
    datos_body_battery = [{"charged": 60, "bodyBatteryValuesArray": []}]
    assert _extraer_nivel_body_battery(datos_body_battery) == 60


def test_extraer_nivel_body_battery_retorna_cero_si_no_hay_datos():
    assert _extraer_nivel_body_battery([]) == 0


def test_construir_horario_hoy_usa_el_dia_de_la_semana_correcto():
    horario = construir_horario_hoy(RUTA_CONFIG_MOCK, FECHA_PRUEBA)

    assert horario.dia_semana == "miercoles"
    assert horario.bloques_fijos == []
    assert len(horario.huecos_libres) == 1


def _construir_ruta_config_con_rango_de_semestre(tmp_path):
    with open(RUTA_CONFIG_MOCK, encoding="utf-8") as archivo:
        configuracion = yaml.safe_load(archivo)
    configuracion["fecha_inicio_semestre"] = "2026-08-03"
    configuracion["fecha_fin_semestre"] = "2026-11-28"
    ruta_config_prueba = tmp_path / "config.yaml"
    with open(ruta_config_prueba, "w", encoding="utf-8") as archivo:
        yaml.safe_dump(configuracion, archivo)
    return str(ruta_config_prueba)


def test_construir_horario_hoy_antes_del_semestre_ignora_bloques_fijos(tmp_path):
    ruta_config_prueba = _construir_ruta_config_con_rango_de_semestre(tmp_path)
    fecha_antes_del_semestre = date(2026, 7, 13)

    horario = construir_horario_hoy(ruta_config_prueba, fecha_antes_del_semestre)

    assert horario.dia_semana == "lunes"
    assert horario.bloques_fijos == []
    assert len(horario.huecos_libres) == 1
    assert horario.huecos_libres[0].hora_inicio == time(0, 0)
    assert horario.huecos_libres[0].hora_fin == time(23, 59)


def test_construir_horario_hoy_dentro_del_semestre_respeta_bloques_fijos(tmp_path):
    ruta_config_prueba = _construir_ruta_config_con_rango_de_semestre(tmp_path)
    fecha_dentro_del_semestre = date(2026, 8, 3)

    horario = construir_horario_hoy(ruta_config_prueba, fecha_dentro_del_semestre)

    assert horario.dia_semana == "lunes"
    assert len(horario.bloques_fijos) == 2


def test_construir_horario_hoy_despues_del_semestre_ignora_bloques_fijos(tmp_path):
    ruta_config_prueba = _construir_ruta_config_con_rango_de_semestre(tmp_path)
    fecha_despues_del_semestre = date(2026, 12, 7)

    horario = construir_horario_hoy(ruta_config_prueba, fecha_despues_del_semestre)

    assert horario.bloques_fijos == []
    assert len(horario.huecos_libres) == 1


def test_ejecutar_genera_el_reporte_de_punta_a_punta(tmp_path, cliente_garmin_falso):
    ruta_config_prueba = _construir_ruta_config_de_prueba(tmp_path)
    ruta_salida = tmp_path / "hoy.md"

    ruta_generada = ejecutar(
        fecha=FECHA_PRUEBA,
        ruta_config=ruta_config_prueba,
        ruta_salida=str(ruta_salida),
        cliente_garmin=cliente_garmin_falso,
    )

    assert ruta_generada == str(ruta_salida)
    contenido = ruta_salida.read_text(encoding="utf-8")
    assert "Reporte del dia" in contenido
    assert "Entrenamiento de hoy" in contenido
    assert "Estado fisiologico" in contenido
