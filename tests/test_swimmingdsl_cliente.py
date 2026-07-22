from datetime import date
from unittest.mock import MagicMock, patch

import pytest
import requests

from fuentes.swimmingdsl_cliente import ClienteSwimmingDSL, construir_sesion_desde_resultado, parsear_codigo_dsl

CODIGO_CON_SECCIONES = """session generated_speed {
  warmup {
    swim 500 m easy pace 120
  }
  main {
    30 x swim 50 m butterfly hard pace 60 rest 45 s
  }
  cooldown {
    swim 500 m easy pace 130
  }
}"""

CODIGO_SIN_SECCIONES = """session generated_recovery {
  swim 3000 m easy pace 140
}"""

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


def test_parsear_codigo_dsl_con_secciones_explicitas():
    bloques = parsear_codigo_dsl(CODIGO_CON_SECCIONES)

    assert len(bloques) == 3

    calentamiento = bloques[0]
    assert calentamiento.seccion == "warmup"
    assert calentamiento.repeticiones == 1
    assert calentamiento.distancia_m == 500
    assert calentamiento.estilo is None
    assert calentamiento.intensidad == "easy"
    assert calentamiento.pace_segundos == 120
    assert calentamiento.descanso_segundos is None

    principal = bloques[1]
    assert principal.seccion == "main"
    assert principal.repeticiones == 30
    assert principal.distancia_m == 50
    assert principal.estilo == "butterfly"
    assert principal.intensidad == "hard"
    assert principal.pace_segundos == 60
    assert principal.descanso_segundos == 45

    enfriamiento = bloques[2]
    assert enfriamiento.seccion == "cooldown"
    assert enfriamiento.distancia_m == 500
    assert enfriamiento.pace_segundos == 130


def test_parsear_codigo_dsl_sin_secciones_usa_main_por_defecto():
    bloques = parsear_codigo_dsl(CODIGO_SIN_SECCIONES)

    assert len(bloques) == 1
    assert bloques[0].seccion == "main"
    assert bloques[0].repeticiones == 1
    assert bloques[0].distancia_m == 3000
    assert bloques[0].intensidad == "easy"
    assert bloques[0].pace_segundos == 140
    assert bloques[0].descanso_segundos is None


def test_parsear_codigo_dsl_bloque_sin_repeticion_ni_descanso():
    bloques = parsear_codigo_dsl("session prueba {\n  swim 200 m freestyle moderate pace 100\n}")

    assert len(bloques) == 1
    bloque = bloques[0]
    assert bloque.repeticiones == 1
    assert bloque.descanso_segundos is None
    assert bloque.estilo == "freestyle"
    assert bloque.intensidad == "moderate"


def test_parsear_codigo_dsl_ignora_lineas_vacias():
    codigo = "session prueba {\n\n  swim 100 m pace 90\n\n}"
    bloques = parsear_codigo_dsl(codigo)
    assert len(bloques) == 1
    assert bloques[0].distancia_m == 100
    assert bloques[0].estilo is None
    assert bloques[0].intensidad is None
