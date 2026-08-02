import base64
import json
from datetime import date, timedelta

import anthropic

from modelo.tarea import Tarea

MODELO = "claude-opus-5"

ESQUEMA_EXTRACCION = {
    "type": "object",
    "properties": {
        "parciales": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "titulo": {"type": "string"},
                    "fecha": {"type": "string"},
                    "peso": {"type": "number"},
                },
                "required": ["titulo", "fecha", "peso"],
                "additionalProperties": False,
            },
        },
        "tareas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "titulo": {"type": "string"},
                    "fecha": {"type": "string"},
                    "peso": {"type": "number"},
                },
                "required": ["titulo", "fecha", "peso"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["parciales", "tareas"],
    "additionalProperties": False,
}

PROMPT_EXTRACCION = (
    "Este es el syllabus de un curso universitario. Extrae dos listas: 'parciales' "
    "(examenes, parciales o quices grandes con fecha fija) y 'tareas' (talleres, entregas "
    "o laboratorios con fecha de entrega). Para cada uno incluye titulo, fecha en formato "
    "YYYY-MM-DD y peso como porcentaje numerico de la nota final (si el syllabus no da un "
    "peso exacto, estima uno razonable segun el contexto). Ignora fechas de clases regulares "
    "o festivos."
)

BLOQUES_DE_REPASO = [
    (timedelta(days=7), "Repaso general", "media"),
    (timedelta(days=3), "Practica de ejercicios", "alta"),
    (timedelta(days=1), "Repaso final", "alta"),
]


class ExtraccionSyllabusRechazada(Exception):
    pass


class ClienteSyllabus:
    def __init__(self, cliente=None):
        self.cliente = cliente or anthropic.Anthropic()

    def extraer_fechas_academicas(self, contenido_pdf: bytes) -> dict:
        datos_base64 = base64.standard_b64encode(contenido_pdf).decode("utf-8")
        respuesta = self.cliente.messages.create(
            model=MODELO,
            max_tokens=4096,
            output_config={"format": {"type": "json_schema", "schema": ESQUEMA_EXTRACCION}},
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": datos_base64,
                            },
                        },
                        {"type": "text", "text": PROMPT_EXTRACCION},
                    ],
                }
            ],
        )
        if respuesta.stop_reason == "refusal":
            raise ExtraccionSyllabusRechazada("Claude no pudo procesar este syllabus (rechazado por seguridad).")

        texto = next(bloque.text for bloque in respuesta.content if bloque.type == "text")
        return json.loads(texto)


def construir_tareas_desde_extraccion(extraccion: dict, curso: str) -> list[Tarea]:
    tareas = []
    for entrada in extraccion.get("tareas", []):
        tareas.append(
            Tarea(
                curso=curso,
                titulo=entrada["titulo"],
                fecha_limite=date.fromisoformat(entrada["fecha"]),
                energia_requerida="media",
                peso_academico=float(entrada["peso"]),
                estado="pendiente",
            )
        )

    for parcial in extraccion.get("parciales", []):
        fecha_parcial = date.fromisoformat(parcial["fecha"])
        for delta, prefijo, energia in BLOQUES_DE_REPASO:
            tareas.append(
                Tarea(
                    curso=curso,
                    titulo=f"{prefijo}: {parcial['titulo']}",
                    fecha_limite=fecha_parcial - delta,
                    energia_requerida=energia,
                    peso_academico=float(parcial["peso"]),
                    estado="pendiente",
                    detalles=f"Bloque de estudio generado automaticamente para {parcial['titulo']} ({fecha_parcial.isoformat()}).",
                )
            )

    return tareas
