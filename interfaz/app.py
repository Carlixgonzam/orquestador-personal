import os
from datetime import date

from flask import Flask, redirect, render_template, request, url_for

from fuentes.cursos_cliente import cargar_nombres_cursos
from fuentes.entrenamiento_cliente import (
    actualizar_sesion,
    agregar_sesion,
    cargar_plan_semana_actual,
    eliminar_sesion,
    nombre_archivo_plan_semana_actual,
)
from fuentes.historial_cliente import cargar_historial
from fuentes.notas_cliente import hallazgos_por_curso
from fuentes.pendientes_cliente import (
    actualizar_estado_tarea,
    actualizar_tarea,
    agregar_tarea,
    cargar_todas_las_tareas,
    eliminar_tarea,
)
from interfaz.graficas import generar_graficas_de_historial
from modelo.sesion_entrenamiento import SesionEntrenamiento
from modelo.tarea import Tarea
from scripts.ejecutar_diario import (
    RUTA_CONFIG_POR_DEFECTO,
    RUTA_HISTORIAL_POR_DEFECTO,
    RUTA_SALIDA_POR_DEFECTO,
    _cargar_configuracion,
    ejecutar,
)

app = Flask(__name__, template_folder="plantillas", static_folder="estaticos")


def _ruta_repo_pendientes() -> str:
    configuracion = _cargar_configuracion(RUTA_CONFIG_POR_DEFECTO)
    return configuracion["rutas_repos"]["pendientes"]


def _ruta_repo_entrenamiento() -> str:
    configuracion = _cargar_configuracion(RUTA_CONFIG_POR_DEFECTO)
    return configuracion["rutas_repos"]["entrenamiento"]


def _sesiones_ordenadas_con_indice():
    sesiones_indexadas = list(enumerate(cargar_plan_semana_actual(_ruta_repo_entrenamiento())))
    return sorted(sesiones_indexadas, key=lambda par: par[1].fecha)


def _repos_notas() -> list[dict]:
    configuracion = _cargar_configuracion(RUTA_CONFIG_POR_DEFECTO)
    return configuracion.get("repos_notas", [])


def _nombres_cursos() -> dict[str, str]:
    return cargar_nombres_cursos(RUTA_CONFIG_POR_DEFECTO)


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
        nombres_cursos=_nombres_cursos(),
    )


@app.route("/rendimiento")
def rendimiento():
    filas = cargar_historial(RUTA_HISTORIAL_POR_DEFECTO)
    return render_template(
        "rendimiento.html",
        filas=filas,
        graficas=generar_graficas_de_historial(filas),
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


@app.route("/tareas/<int:indice>/editar", methods=["GET"])
def formulario_editar_tarea(indice: int):
    tareas = cargar_todas_las_tareas(_ruta_repo_pendientes())
    return render_template(
        "editar_tarea.html",
        indice=indice,
        tarea=tareas[indice],
        nombres_cursos=_nombres_cursos(),
    )


@app.route("/tareas/<int:indice>/editar", methods=["POST"])
def guardar_edicion_tarea(indice: int):
    tarea_actualizada = Tarea(
        curso=request.form["curso"],
        titulo=request.form["titulo"],
        fecha_limite=date.fromisoformat(request.form["fecha_limite"]),
        energia_requerida=request.form["energia_requerida"],
        peso_academico=float(request.form["peso_academico"]),
        estado=request.form["estado"],
    )
    actualizar_tarea(_ruta_repo_pendientes(), indice, tarea_actualizada)
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


@app.route("/entrenamiento")
def entrenamiento():
    return render_template(
        "entrenamiento.html",
        sesiones=_sesiones_ordenadas_con_indice(),
        nombre_archivo=nombre_archivo_plan_semana_actual(),
    )


@app.route("/entrenamiento", methods=["POST"])
def crear_sesion():
    sesion_nueva = SesionEntrenamiento(
        fecha=date.fromisoformat(request.form["fecha"]),
        tipo=request.form["tipo"],
        intensidad=request.form["intensidad"],
        notas=request.form["notas"],
    )
    agregar_sesion(_ruta_repo_entrenamiento(), sesion_nueva)
    return redirect(url_for("entrenamiento"))


@app.route("/entrenamiento/<int:indice>/editar", methods=["GET"])
def formulario_editar_sesion(indice: int):
    sesiones = cargar_plan_semana_actual(_ruta_repo_entrenamiento())
    return render_template("editar_sesion.html", indice=indice, sesion=sesiones[indice])


@app.route("/entrenamiento/<int:indice>/editar", methods=["POST"])
def guardar_edicion_sesion(indice: int):
    sesion_actualizada = SesionEntrenamiento(
        fecha=date.fromisoformat(request.form["fecha"]),
        tipo=request.form["tipo"],
        intensidad=request.form["intensidad"],
        notas=request.form["notas"],
    )
    actualizar_sesion(_ruta_repo_entrenamiento(), date.today(), indice, sesion_actualizada)
    return redirect(url_for("entrenamiento"))


@app.route("/entrenamiento/<int:indice>/eliminar", methods=["POST"])
def borrar_sesion(indice: int):
    eliminar_sesion(_ruta_repo_entrenamiento(), date.today(), indice)
    return redirect(url_for("entrenamiento"))


if __name__ == "__main__":
    app.run(debug=True, port=5050)
