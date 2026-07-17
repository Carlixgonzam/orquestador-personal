import os
from datetime import date

import yaml

from modelo.tarea import Tarea

NOMBRE_ARCHIVO_TAREAS = "tareas.yaml"
ESTADOS_FINALIZADOS = {"completada", "cancelada"}


def _tarea_desde_diccionario(datos: dict) -> Tarea:
    return Tarea(
        curso=datos["curso"],
        titulo=datos["titulo"],
        fecha_limite=date.fromisoformat(str(datos["fecha_limite"])),
        energia_requerida=datos["energia_requerida"],
        peso_academico=float(datos["peso_academico"]),
        estado=datos["estado"],
    )


def cargar_todas_las_tareas(ruta_repo_pendientes: str) -> list[Tarea]:
    ruta_archivo = os.path.join(ruta_repo_pendientes, NOMBRE_ARCHIVO_TAREAS)
    with open(ruta_archivo, encoding="utf-8") as archivo_tareas:
        contenido = yaml.safe_load(archivo_tareas)

    tareas_crudas = contenido.get("tareas", [])
    return [_tarea_desde_diccionario(tarea) for tarea in tareas_crudas]


def cargar_tareas_pendientes(ruta_repo_pendientes: str) -> list[Tarea]:
    todas_las_tareas = cargar_todas_las_tareas(ruta_repo_pendientes)
    return [tarea for tarea in todas_las_tareas if tarea.estado not in ESTADOS_FINALIZADOS]
