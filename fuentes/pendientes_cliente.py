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


def _tarea_a_diccionario(tarea: Tarea) -> dict:
    return {
        "curso": tarea.curso,
        "titulo": tarea.titulo,
        "fecha_limite": tarea.fecha_limite.isoformat(),
        "energia_requerida": tarea.energia_requerida,
        "peso_academico": tarea.peso_academico,
        "estado": tarea.estado,
    }


def cargar_todas_las_tareas(ruta_repo_pendientes: str) -> list[Tarea]:
    ruta_archivo = os.path.join(ruta_repo_pendientes, NOMBRE_ARCHIVO_TAREAS)
    with open(ruta_archivo, encoding="utf-8") as archivo_tareas:
        contenido = yaml.safe_load(archivo_tareas)

    tareas_crudas = contenido.get("tareas", [])
    return [_tarea_desde_diccionario(tarea) for tarea in tareas_crudas]


def cargar_tareas_pendientes(ruta_repo_pendientes: str) -> list[Tarea]:
    todas_las_tareas = cargar_todas_las_tareas(ruta_repo_pendientes)
    return [tarea for tarea in todas_las_tareas if tarea.estado not in ESTADOS_FINALIZADOS]


def guardar_todas_las_tareas(ruta_repo_pendientes: str, tareas: list[Tarea]) -> None:
    ruta_archivo = os.path.join(ruta_repo_pendientes, NOMBRE_ARCHIVO_TAREAS)
    contenido = {"tareas": [_tarea_a_diccionario(tarea) for tarea in tareas]}
    with open(ruta_archivo, "w", encoding="utf-8") as archivo_tareas:
        yaml.safe_dump(contenido, archivo_tareas, allow_unicode=True, sort_keys=False)


def agregar_tarea(ruta_repo_pendientes: str, tarea_nueva: Tarea) -> None:
    tareas = cargar_todas_las_tareas(ruta_repo_pendientes)
    tareas.append(tarea_nueva)
    guardar_todas_las_tareas(ruta_repo_pendientes, tareas)


def actualizar_estado_tarea(ruta_repo_pendientes: str, indice: int, nuevo_estado: str) -> None:
    tareas = cargar_todas_las_tareas(ruta_repo_pendientes)
    tareas[indice].estado = nuevo_estado
    guardar_todas_las_tareas(ruta_repo_pendientes, tareas)


def eliminar_tarea(ruta_repo_pendientes: str, indice: int) -> None:
    tareas = cargar_todas_las_tareas(ruta_repo_pendientes)
    del tareas[indice]
    guardar_todas_las_tareas(ruta_repo_pendientes, tareas)
