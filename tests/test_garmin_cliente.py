import json
import os
from datetime import date
from unittest.mock import MagicMock

import pytest

from fuentes.garmin_cliente import ClienteGarmin
from fuentes.garmin_workout_builder import construir_workout_natacion
from fuentes.swimmingdsl_cliente import BloqueNado

RUTA_MOCK = os.path.join(os.path.dirname(__file__), "fixtures", "garmin_mock.json")
FECHA_PRUEBA = date(2026, 8, 3)


@pytest.fixture
def datos_mock():
    with open(RUTA_MOCK, encoding="utf-8") as archivo_mock:
        return json.load(archivo_mock)


@pytest.fixture
def cliente_garmin_falso(datos_mock):
    cliente_falso = MagicMock()
    cliente_falso.get_training_readiness.return_value = datos_mock["training_readiness"]
    cliente_falso.get_hrv_data.return_value = datos_mock["hrv_data"]
    cliente_falso.get_training_status.return_value = datos_mock["training_status"]
    cliente_falso.get_max_metrics.return_value = datos_mock["max_metrics"]
    cliente_falso.get_endurance_score.return_value = datos_mock["endurance_score"]
    cliente_falso.get_race_predictions.return_value = datos_mock["race_predictions"]
    cliente_falso.get_rhr_day.return_value = datos_mock["rhr_day"]
    cliente_falso.get_respiration_data.return_value = datos_mock["respiration_data"]
    cliente_falso.get_stress_data.return_value = datos_mock["stress_data"]
    cliente_falso.get_body_battery_events.return_value = datos_mock["body_battery_events"]
    cliente_falso.get_body_battery.return_value = datos_mock["body_battery"]
    return cliente_falso


@pytest.fixture
def cliente_garmin(cliente_garmin_falso):
    return ClienteGarmin(cliente_garmin=cliente_garmin_falso)


def test_cliente_garmin_no_se_autentica_cuando_recibe_cliente_inyectado(cliente_garmin_falso):
    ClienteGarmin(cliente_garmin=cliente_garmin_falso)
    cliente_garmin_falso.login.assert_not_called()


def test_obtener_disposicion_entrenamiento_delega_con_la_fecha_correcta(cliente_garmin, cliente_garmin_falso, datos_mock):
    resultado = cliente_garmin.obtener_disposicion_entrenamiento(FECHA_PRUEBA)
    cliente_garmin_falso.get_training_readiness.assert_called_once_with("2026-08-03")
    assert resultado == datos_mock["training_readiness"]


def test_obtener_hrv_delega_con_la_fecha_correcta(cliente_garmin, cliente_garmin_falso, datos_mock):
    resultado = cliente_garmin.obtener_hrv(FECHA_PRUEBA)
    cliente_garmin_falso.get_hrv_data.assert_called_once_with("2026-08-03")
    assert resultado == datos_mock["hrv_data"]


def test_obtener_estado_entrenamiento_incluye_balance_de_carga(cliente_garmin, cliente_garmin_falso, datos_mock):
    resultado = cliente_garmin.obtener_estado_entrenamiento(FECHA_PRUEBA)
    cliente_garmin_falso.get_training_status.assert_called_once_with("2026-08-03")
    assert resultado == datos_mock["training_status"]
    assert "mostRecentTrainingLoadBalance" in resultado


def test_obtener_metricas_maximas_delega_con_la_fecha_correcta(cliente_garmin, cliente_garmin_falso, datos_mock):
    resultado = cliente_garmin.obtener_metricas_maximas(FECHA_PRUEBA)
    cliente_garmin_falso.get_max_metrics.assert_called_once_with("2026-08-03")
    assert resultado == datos_mock["max_metrics"]


def test_obtener_score_resistencia_delega_con_la_fecha_correcta(cliente_garmin, cliente_garmin_falso, datos_mock):
    resultado = cliente_garmin.obtener_score_resistencia(FECHA_PRUEBA)
    cliente_garmin_falso.get_endurance_score.assert_called_once_with("2026-08-03")
    assert resultado == datos_mock["endurance_score"]


def test_obtener_predicciones_carrera_no_requiere_fecha(cliente_garmin, cliente_garmin_falso, datos_mock):
    resultado = cliente_garmin.obtener_predicciones_carrera()
    cliente_garmin_falso.get_race_predictions.assert_called_once_with()
    assert resultado == datos_mock["race_predictions"]


def test_obtener_frecuencia_cardiaca_reposo_delega_con_la_fecha_correcta(cliente_garmin, cliente_garmin_falso, datos_mock):
    resultado = cliente_garmin.obtener_frecuencia_cardiaca_reposo(FECHA_PRUEBA)
    cliente_garmin_falso.get_rhr_day.assert_called_once_with("2026-08-03")
    assert resultado == datos_mock["rhr_day"]


def test_obtener_frecuencia_respiratoria_delega_con_la_fecha_correcta(cliente_garmin, cliente_garmin_falso, datos_mock):
    resultado = cliente_garmin.obtener_frecuencia_respiratoria(FECHA_PRUEBA)
    cliente_garmin_falso.get_respiration_data.assert_called_once_with("2026-08-03")
    assert resultado == datos_mock["respiration_data"]


def test_obtener_estres_delega_con_la_fecha_correcta(cliente_garmin, cliente_garmin_falso, datos_mock):
    resultado = cliente_garmin.obtener_estres(FECHA_PRUEBA)
    cliente_garmin_falso.get_stress_data.assert_called_once_with("2026-08-03")
    assert resultado == datos_mock["stress_data"]


def test_obtener_eventos_body_battery_delega_con_la_fecha_correcta(cliente_garmin, cliente_garmin_falso, datos_mock):
    resultado = cliente_garmin.obtener_eventos_body_battery(FECHA_PRUEBA)
    cliente_garmin_falso.get_body_battery_events.assert_called_once_with("2026-08-03")
    assert resultado == datos_mock["body_battery_events"]


def test_obtener_nivel_body_battery_delega_con_la_fecha_correcta(cliente_garmin, cliente_garmin_falso, datos_mock):
    resultado = cliente_garmin.obtener_nivel_body_battery(FECHA_PRUEBA)
    cliente_garmin_falso.get_body_battery.assert_called_once_with("2026-08-03")
    assert resultado == datos_mock["body_battery"]


def test_metodos_sin_fecha_explicita_usan_la_fecha_de_hoy(cliente_garmin, cliente_garmin_falso):
    cliente_garmin.obtener_hrv()
    cliente_garmin_falso.get_hrv_data.assert_called_once_with(date.today().isoformat())


def test_subir_entrenamiento_natacion_delega_el_workout_y_retorna_la_respuesta(cliente_garmin, cliente_garmin_falso):
    bloques = [BloqueNado(seccion="main", repeticiones=1, distancia_m=200, estilo="freestyle", intensidad="moderate", pace_segundos=100, descanso_segundos=None)]
    workout = construir_workout_natacion("Prueba", bloques)
    cliente_garmin_falso.upload_swimming_workout.return_value = {"workoutId": 42}

    resultado = cliente_garmin.subir_entrenamiento_natacion(workout)

    cliente_garmin_falso.upload_swimming_workout.assert_called_once_with(workout)
    assert resultado == {"workoutId": 42}


def test_programar_entrenamiento_delega_con_id_y_fecha_en_texto(cliente_garmin, cliente_garmin_falso):
    cliente_garmin_falso.schedule_workout.return_value = {"scheduled": True}

    resultado = cliente_garmin.programar_entrenamiento(42, FECHA_PRUEBA)

    cliente_garmin_falso.schedule_workout.assert_called_once_with(42, "2026-08-03")
    assert resultado == {"scheduled": True}
