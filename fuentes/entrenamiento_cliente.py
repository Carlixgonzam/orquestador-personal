import glob
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
    if not os.path.exists(ruta_archivo):
        return []

    with open(ruta_archivo, encoding="utf-8") as archivo_plan:
        contenido = yaml.safe_load(archivo_plan)

    sesiones_crudas = contenido.get("sesiones", [])
    return [_sesion_desde_diccionario(sesion) for sesion in sesiones_crudas]


def cargar_todas_las_sesiones(ruta_repo_entrenamiento: str) -> list[SesionEntrenamiento]:
    patron_archivos = os.path.join(ruta_repo_entrenamiento, "plan-semana-*.yaml")
    sesiones = []
    for ruta_archivo in sorted(glob.glob(patron_archivos)):
        with open(ruta_archivo, encoding="utf-8") as archivo_plan:
            contenido = yaml.safe_load(archivo_plan)
        sesiones_crudas = (contenido or {}).get("sesiones", [])
        sesiones.extend(_sesion_desde_diccionario(sesion) for sesion in sesiones_crudas)
    sesiones.sort(key=lambda sesion: sesion.fecha)
    return sesiones


def obtener_sesion_de_hoy(sesiones: list[SesionEntrenamiento], fecha: date | None = None) -> SesionEntrenamiento | None:
    fecha_referencia = fecha or date.today()
    for sesion in sesiones:
        if sesion.fecha == fecha_referencia:
            return sesion
    return None


def _sesion_a_diccionario(sesion: SesionEntrenamiento) -> dict:
    return {
        "fecha": sesion.fecha.isoformat(),
        "tipo": sesion.tipo,
        "intensidad": sesion.intensidad,
        "notas": sesion.notas,
    }


def guardar_plan_semana(ruta_repo_entrenamiento: str, fecha: date, sesiones: list[SesionEntrenamiento]) -> None:
    nombre_archivo = nombre_archivo_plan_semana_actual(fecha)
    ruta_archivo = os.path.join(ruta_repo_entrenamiento, nombre_archivo)
    contenido = {"sesiones": [_sesion_a_diccionario(sesion) for sesion in sesiones]}
    with open(ruta_archivo, "w", encoding="utf-8") as archivo_plan:
        yaml.safe_dump(contenido, archivo_plan, allow_unicode=True, sort_keys=False)


def agregar_sesion(ruta_repo_entrenamiento: str, sesion_nueva: SesionEntrenamiento) -> None:
    sesiones = cargar_plan_semana_actual(ruta_repo_entrenamiento, sesion_nueva.fecha)
    sesiones.append(sesion_nueva)
    guardar_plan_semana(ruta_repo_entrenamiento, sesion_nueva.fecha, sesiones)


def actualizar_sesion(
    ruta_repo_entrenamiento: str, fecha_semana: date, indice: int, sesion_actualizada: SesionEntrenamiento
) -> None:
    sesiones = cargar_plan_semana_actual(ruta_repo_entrenamiento, fecha_semana)
    sesiones[indice] = sesion_actualizada
    guardar_plan_semana(ruta_repo_entrenamiento, fecha_semana, sesiones)


def eliminar_sesion(ruta_repo_entrenamiento: str, fecha_semana: date, indice: int) -> None:
    sesiones = cargar_plan_semana_actual(ruta_repo_entrenamiento, fecha_semana)
    del sesiones[indice]
    guardar_plan_semana(ruta_repo_entrenamiento, fecha_semana, sesiones)
