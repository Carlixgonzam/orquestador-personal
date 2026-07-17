import os
from datetime import date

from flask import Flask, redirect, render_template, request, url_for

from fuentes.notas_cliente import hallazgos_por_curso
from fuentes.pendientes_cliente import (
    actualizar_estado_tarea,
    agregar_tarea,
    cargar_todas_las_tareas,
    eliminar_tarea,
)
from modelo.tarea import Tarea
from scripts.ejecutar_diario import RUTA_CONFIG_POR_DEFECTO, RUTA_SALIDA_POR_DEFECTO, _cargar_configuracion, ejecutar

app = Flask(__name__, template_folder="plantillas")


def _ruta_repo_pendientes() -> str:
    configuracion = _cargar_configuracion(RUTA_CONFIG_POR_DEFECTO)
    return configuracion["rutas_repos"]["pendientes"]


def _repos_notas() -> list[dict]:
    configuracion = _cargar_configuracion(RUTA_CONFIG_POR_DEFECTO)
    return configuracion.get("repos_notas", [])


def _leer_contenido_hoy() -> str:
    if not os.path.exists(RUTA_SALIDA_POR_DEFECTO):
        return "Aun no se ha generado ningun reporte. Presiona 'Regenerar con Garmin' para crear el primero."
    with open(RUTA_SALIDA_POR_DEFECTO, encoding="utf-8") as archivo_hoy:
        return archivo_hoy.read()


def _tareas_ordenadas_por_deadline_con_indice():
    tareas_indexadas = list(enumerate(cargar_todas_las_tareas(_ruta_repo_pendientes())))
    return sorted(tareas_indexadas, key=lambda par: par[1].fecha_limite)


@app.route("/")
def index():
    return render_template(
        "index.html",
        tareas=_tareas_ordenadas_por_deadline_con_indice(),
        contenido_hoy=_leer_contenido_hoy(),
        hallazgos_por_curso=hallazgos_por_curso(_repos_notas()),
    )


@app.route("/tareas", methods=["POST"])
def crear_tarea():
    tarea_nueva = Tarea(
        curso=request.form["curso"],
        titulo=request.form["titulo"],
        fecha_limite=date.fromisoformat(request.form["fecha_limite"]),
        energia_requerida=request.form["energia_requerida"],
        peso_academico=float(request.form["peso_academico"]),
        estado="pendiente",
    )
    agregar_tarea(_ruta_repo_pendientes(), tarea_nueva)
    return redirect(url_for("index"))


@app.route("/tareas/<int:indice>/completar", methods=["POST"])
def completar_tarea(indice: int):
    actualizar_estado_tarea(_ruta_repo_pendientes(), indice, "completada")
    return redirect(url_for("index"))


@app.route("/tareas/<int:indice>/eliminar", methods=["POST"])
def borrar_tarea(indice: int):
    eliminar_tarea(_ruta_repo_pendientes(), indice)
    return redirect(url_for("index"))


@app.route("/regenerar", methods=["POST"])
def regenerar_reporte():
    ejecutar()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=5050)
