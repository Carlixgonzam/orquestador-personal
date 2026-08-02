import json
from datetime import date
from unittest.mock import MagicMock

import pytest

from fuentes.syllabus_cliente import (
    ClienteSyllabus,
    ExtraccionSyllabusRechazada,
    construir_tareas_desde_extraccion,
)

EXTRACCION_PRUEBA = {
    "parciales": [{"titulo": "Primer parcial", "fecha": "2026-09-15", "peso": 20.0}],
    "tareas": [{"titulo": "Taller 1", "fecha": "2026-08-20", "peso": 5.0}],
}


def _bloque_texto(contenido: dict):
    bloque = MagicMock()
    bloque.type = "text"
    bloque.text = json.dumps(contenido)
    return bloque


def test_extraer_fechas_academicas_retorna_el_json_parseado():
    cliente_falso = MagicMock()
    respuesta_falsa = MagicMock()
    respuesta_falsa.stop_reason = "end_turn"
    respuesta_falsa.content = [_bloque_texto(EXTRACCION_PRUEBA)]
    cliente_falso.messages.create.return_value = respuesta_falsa

    cliente_syllabus = ClienteSyllabus(cliente=cliente_falso)
    resultado = cliente_syllabus.extraer_fechas_academicas(b"contenido pdf falso")

    assert resultado == EXTRACCION_PRUEBA


def test_extraer_fechas_academicas_envia_el_pdf_en_base64():
    cliente_falso = MagicMock()
    respuesta_falsa = MagicMock()
    respuesta_falsa.stop_reason = "end_turn"
    respuesta_falsa.content = [_bloque_texto(EXTRACCION_PRUEBA)]
    cliente_falso.messages.create.return_value = respuesta_falsa

    cliente_syllabus = ClienteSyllabus(cliente=cliente_falso)
    cliente_syllabus.extraer_fechas_academicas(b"hola")

    argumentos = cliente_falso.messages.create.call_args.kwargs
    bloque_documento = argumentos["messages"][0]["content"][0]
    assert bloque_documento["type"] == "document"
    assert bloque_documento["source"]["media_type"] == "application/pdf"


def test_extraer_fechas_academicas_lanza_error_si_hay_rechazo():
    cliente_falso = MagicMock()
    respuesta_falsa = MagicMock()
    respuesta_falsa.stop_reason = "refusal"
    cliente_falso.messages.create.return_value = respuesta_falsa

    cliente_syllabus = ClienteSyllabus(cliente=cliente_falso)
    with pytest.raises(ExtraccionSyllabusRechazada):
        cliente_syllabus.extraer_fechas_academicas(b"contenido")


def test_construir_tareas_mapea_las_tareas_directamente():
    tareas = construir_tareas_desde_extraccion(EXTRACCION_PRUEBA, "matematica")

    tarea_taller = next(t for t in tareas if t.titulo == "Taller 1")
    assert tarea_taller.curso == "matematica"
    assert tarea_taller.fecha_limite == date(2026, 8, 20)
    assert tarea_taller.peso_academico == 5.0
    assert tarea_taller.estado == "pendiente"


def test_construir_tareas_genera_tres_bloques_de_estudio_por_parcial():
    tareas = construir_tareas_desde_extraccion(EXTRACCION_PRUEBA, "matematica")

    bloques = [t for t in tareas if "Primer parcial" in t.titulo]
    assert len(bloques) == 3
    fechas = sorted(bloque.fecha_limite for bloque in bloques)
    assert fechas == [date(2026, 9, 8), date(2026, 9, 12), date(2026, 9, 14)]
    assert all(bloque.peso_academico == 20.0 for bloque in bloques)


def test_construir_tareas_sin_parciales_ni_tareas_retorna_lista_vacia():
    assert construir_tareas_desde_extraccion({"parciales": [], "tareas": []}, "web") == []
