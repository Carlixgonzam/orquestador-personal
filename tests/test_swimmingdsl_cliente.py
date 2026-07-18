from datetime import date
from unittest.mock import MagicMock, patch

import pytest
import requests

from fuentes.swimmingdsl_cliente import ClienteSwimmingDSL, construir_sesion_desde_resultado

RESULTADO_PRUEBA = {
    "success": True,
    "code": "session Entreno1 {\n  warmup 400 freestyle\n}",
    "goal": "endurance",
    "distance": 2000,
}


def test_construir_sesion_desde_resultado_mapea_los_campos():
    sesion = construir_sesion_desde_resultado(RESULTADO_PRUEBA, date(2026, 8, 5), 60)

    assert sesion.fecha == date(2026, 8, 5)
    assert sesion.tipo == "natacion"
    assert sesion.intensidad == "moderada"
    assert "endurance" in sesion.notas
    assert "2000m" in sesion.notas
    assert "60min" in sesion.notas
    assert "warmup 400 freestyle" in sesion.notas


@pytest.mark.parametrize(
    "objetivo,intensidad_esperada",
    [("speed", "alta"), ("endurance", "moderada"), ("technique", "baja"), ("recovery", "baja")],
)
def test_construir_sesion_desde_resultado_mapea_intensidad_por_objetivo(objetivo, intensidad_esperada):
    resultado = dict(RESULTADO_PRUEBA, goal=objetivo)
    sesion = construir_sesion_desde_resultado(resultado, date(2026, 8, 5), 60)
    assert sesion.intensidad == intensidad_esperada


def test_generar_sesion_llama_al_endpoint_correcto_y_retorna_el_resultado():
    respuesta_falsa = MagicMock()
    respuesta_falsa.json.return_value = RESULTADO_PRUEBA
    respuesta_falsa.raise_for_status.return_value = None

    with patch("fuentes.swimmingdsl_cliente.requests.post", return_value=respuesta_falsa) as post_falso:
        cliente = ClienteSwimmingDSL(url_base="http://localhost:3000")
        resultado = cliente.generar_sesion("endurance", 2000, ["freestyle"], 60)

    post_falso.assert_called_once_with(
        "http://localhost:3000/api/generate",
        json={"goal": "endurance", "distance": 2000, "styles": ["freestyle"], "duration": 60},
        timeout=35,
    )
    assert resultado == RESULTADO_PRUEBA


def test_generar_sesion_lanza_error_si_success_es_falso():
    respuesta_falsa = MagicMock()
    respuesta_falsa.json.return_value = {"success": False, "error": "objetivo invalido"}
    respuesta_falsa.raise_for_status.return_value = None

    with patch("fuentes.swimmingdsl_cliente.requests.post", return_value=respuesta_falsa):
        cliente = ClienteSwimmingDSL()
        with pytest.raises(RuntimeError, match="objetivo invalido"):
            cliente.generar_sesion("desconocido", 2000, ["freestyle"], 60)


def test_generar_sesion_propaga_error_de_conexion():
    with patch("fuentes.swimmingdsl_cliente.requests.post", side_effect=requests.exceptions.ConnectionError()):
        cliente = ClienteSwimmingDSL()
        with pytest.raises(requests.exceptions.ConnectionError):
            cliente.generar_sesion("endurance", 2000, ["freestyle"], 60)
