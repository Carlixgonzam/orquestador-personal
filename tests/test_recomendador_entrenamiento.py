from datetime import date

import pytest

from modelo.sesion_entrenamiento import SesionEntrenamiento
from motor.recomendador_entrenamiento import (
    MANTENER,
    RECUPERACION_ACTIVA,
    REDUCIR_INTENSIDAD,
    SIN_SESION_PLANEADA,
    decidir_ajuste_entrenamiento,
)

SESION_PRUEBA = SesionEntrenamiento(date(2026, 8, 3), "natacion", "alta", "Series de velocidad")


def test_sin_sesion_planeada_no_sugiere_ajuste():
    recomendacion = decidir_ajuste_entrenamiento("productive", None)
    assert recomendacion.tipo_ajuste == SIN_SESION_PLANEADA
    assert recomendacion.sesion_planeada is None


@pytest.mark.parametrize("training_status", ["overreaching", "detraining", "Overreaching", "DETRAINING"])
def test_estados_criticos_generan_recuperacion_activa(training_status):
    recomendacion = decidir_ajuste_entrenamiento(training_status, SESION_PRUEBA)
    assert recomendacion.tipo_ajuste == RECUPERACION_ACTIVA
    assert recomendacion.sesion_planeada == SESION_PRUEBA


def test_acwr_alto_reduce_intensidad_cuando_el_estado_no_es_critico():
    recomendacion = decidir_ajuste_entrenamiento("productive", SESION_PRUEBA, acwr_alto=True)
    assert recomendacion.tipo_ajuste == REDUCIR_INTENSIDAD


def test_estado_normal_sin_acwr_alto_mantiene_la_sesion():
    recomendacion = decidir_ajuste_entrenamiento("productive", SESION_PRUEBA, acwr_alto=False)
    assert recomendacion.tipo_ajuste == MANTENER


def test_estado_critico_tiene_prioridad_sobre_acwr_alto():
    recomendacion = decidir_ajuste_entrenamiento("overreaching", SESION_PRUEBA, acwr_alto=True)
    assert recomendacion.tipo_ajuste == RECUPERACION_ACTIVA


def test_recomendacion_nunca_cambia_la_sesion_planeada_solo_el_ajuste():
    recomendacion = decidir_ajuste_entrenamiento("maintaining", SESION_PRUEBA, acwr_alto=True)
    assert recomendacion.sesion_planeada is SESION_PRUEBA
