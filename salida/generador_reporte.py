import os

from jinja2 import Environment, FileSystemLoader, select_autoescape

from modelo.estado_fisiologico import EstadoFisiologico
from motor.priorizador import HorarioHoy, ResultadoPriorizacion

RUTA_PLANTILLAS = os.path.join(os.path.dirname(__file__), "plantillas")
NOMBRE_PLANTILLA_REPORTE_DIARIO = "hoy_md.jinja"


def _entorno_plantillas() -> Environment:
    return Environment(
        loader=FileSystemLoader(RUTA_PLANTILLAS),
        autoescape=select_autoescape(enabled_extensions=()),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def generar_contenido_reporte(
    resultado: ResultadoPriorizacion,
    estado_fisiologico: EstadoFisiologico,
    horario_hoy: HorarioHoy,
) -> str:
    plantilla = _entorno_plantillas().get_template(NOMBRE_PLANTILLA_REPORTE_DIARIO)
    return plantilla.render(resultado=resultado, estado=estado_fisiologico, horario=horario_hoy)


def generar_reporte(
    resultado: ResultadoPriorizacion,
    estado_fisiologico: EstadoFisiologico,
    horario_hoy: HorarioHoy,
    ruta_salida: str = "hoy.md",
) -> str:
    contenido = generar_contenido_reporte(resultado, estado_fisiologico, horario_hoy)
    with open(ruta_salida, "w", encoding="utf-8") as archivo_salida:
        archivo_salida.write(contenido)
    return ruta_salida
