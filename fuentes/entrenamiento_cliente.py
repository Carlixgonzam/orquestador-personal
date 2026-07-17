import os
from datetime import date

import yaml

from modelo.sesion_entrenamiento import SesionEntrenamiento


def nombre_archivo_plan_semana_actual(fecha: date | None = None) -> str:
    fecha_referencia = fecha or date.today()
    numero_semana = fecha_referencia.isocalendar().week
    return f"plan-semana-{numero_semana:02d}.yaml"


def _sesion_desde_diccionario(datos: dict) -> SesionEntrenamiento:
    return SesionEntrenamiento(
        fecha=date.fromisoformat(str(datos["fecha"])),
        tipo=datos["tipo"],
        intensidad=datos["intensidad"],
        notas=datos.get("notas", ""),
    )


def cargar_plan_semana_actual(ruta_repo_entrenamiento: str, fecha: date | None = None) -> list[SesionEntrenamiento]:
    nombre_archivo = nombre_archivo_plan_semana_actual(fecha)
    ruta_archivo = os.path.join(ruta_repo_entrenamiento, nombre_archivo)
    with open(ruta_archivo, encoding="utf-8") as archivo_plan:
        contenido = yaml.safe_load(archivo_plan)

    sesiones_crudas = contenido.get("sesiones", [])
    return [_sesion_desde_diccionario(sesion) for sesion in sesiones_crudas]


def obtener_sesion_de_hoy(sesiones: list[SesionEntrenamiento], fecha: date | None = None) -> SesionEntrenamiento | None:
    fecha_referencia = fecha or date.today()
    for sesion in sesiones:
        if sesion.fecha == fecha_referencia:
            return sesion
    return None
