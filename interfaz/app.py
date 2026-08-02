import os
from datetime import date, timedelta

import requests
from flask import Flask, flash, redirect, render_template, request, url_for

from fuentes.cursos_cliente import cargar_nombres_cursos
from fuentes.entrenamiento_cliente import (
    actualizar_sesion,
    agregar_sesion,
    cargar_plan_semana_actual,
    cargar_todas_las_sesiones,
    eliminar_sesion,
    nombre_archivo_plan_semana_actual,
)
from fuentes.garmin_cliente import ClienteGarmin
from fuentes.garmin_workout_builder import construir_workout_natacion
from fuentes.historial_cliente import cargar_historial
from fuentes.horario_cliente import DIAS_SEMANA
from fuentes.notas_cliente import hallazgos_por_curso
from fuentes.pendientes_cliente import (
    actualizar_estado_tarea,
    actualizar_tarea,
    agregar_tarea,
    cargar_todas_las_tareas,
    eliminar_tarea,
)
from fuentes.swimmingdsl_cliente import ClienteSwimmingDSL, construir_sesion_desde_resultado, parsear_codigo_dsl
from fuentes.syllabus_cliente import ClienteSyllabus, construir_tareas_desde_extraccion
from interfaz.graficas import (
    calcular_fitness_fatiga_forma,
    generar_graficas_de_historial,
    generar_heatmap_entrenamientos,
    generar_svg_pmc,
)
from interfaz.vista_semanal import calcular_lunes_de_la_semana, construir_vista_semanal
from modelo.sesion_entrenamiento import SesionEntrenamiento
from modelo.tarea import Tarea
from motor.agente_entrenamiento import sugerir_parametros_sesion
from salida.snapshot_diario import cargar_snapshot_diario
from scripts.ejecutar_diario import (
    RUTA_CONFIG_POR_DEFECTO,
    RUTA_HISTORIAL_POR_DEFECTO,
    RUTA_SNAPSHOT_POR_DEFECTO,
    _cargar_configuracion,
    construir_estado_fisiologico,
    construir_horario_hoy,
    ejecutar,
)

app = Flask(__name__, template_folder="plantillas", static_folder="estaticos")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))


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


def _extraer_codigo_dsl(notas: str) -> str | None:
    marcador = "swimmingdsl ("
    if marcador not in notas or "\n" not in notas:
        return None
    return notas.split("\n", 1)[1]


def _cargar_snapshot_hoy() -> dict | None:
    return cargar_snapshot_diario(RUTA_SNAPSHOT_POR_DEFECTO)


def _tareas_ordenadas_por_deadline_con_indice():
    tareas_indexadas = list(enumerate(cargar_todas_las_tareas(_ruta_repo_pendientes())))
    return sorted(tareas_indexadas, key=lambda par: par[1].fecha_limite)


def _bloques_fijos_por_dia_de_la_semana(lunes: date) -> dict[str, list]:
    bloques_por_dia = {}
    for indice, nombre_dia in enumerate(DIAS_SEMANA):
        fecha_dia = lunes + timedelta(days=indice)
        horario_del_dia = construir_horario_hoy(RUTA_CONFIG_POR_DEFECTO, fecha_dia)
        bloques_por_dia[nombre_dia] = horario_del_dia.bloques_fijos
    return bloques_por_dia


@app.route("/")
def index():
    return render_template(
        "index.html",
        tareas=_tareas_ordenadas_por_deadline_con_indice(),
        snapshot=_cargar_snapshot_hoy(),
        hallazgos_por_curso=hallazgos_por_curso(_repos_notas()),
        nombres_cursos=_nombres_cursos(),
    )


@app.route("/semana")
def semana():
    lunes = calcular_lunes_de_la_semana(date.today())
    bloques_fijos_por_dia = _bloques_fijos_por_dia_de_la_semana(lunes)
    sesiones_semana = cargar_plan_semana_actual(_ruta_repo_entrenamiento())
    tareas = cargar_todas_las_tareas(_ruta_repo_pendientes())
    dias = construir_vista_semanal(lunes, bloques_fijos_por_dia, sesiones_semana, tareas)
    return render_template("semana.html", dias=dias, nombres_cursos=_nombres_cursos(), hoy=date.today())


@app.route("/rendimiento")
def rendimiento():
    filas = cargar_historial(RUTA_HISTORIAL_POR_DEFECTO)
    fechas_pmc, fitness, fatiga, forma = calcular_fitness_fatiga_forma(filas)
    sesiones = cargar_todas_las_sesiones(_ruta_repo_entrenamiento())
    return render_template(
        "rendimiento.html",
        filas=filas,
        graficas=generar_graficas_de_historial(filas),
        grafica_pmc=generar_svg_pmc(fechas_pmc, fitness, fatiga, forma),
        heatmap_entrenamientos=generar_heatmap_entrenamientos(sesiones, date.today()),
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
        detalles=request.form.get("detalles", ""),
    )
    agregar_tarea(_ruta_repo_pendientes(), tarea_nueva)
    return redirect(url_for("index"))


@app.route("/tareas/subir-syllabus", methods=["POST"])
def subir_syllabus():
    curso = request.form["curso"]
    archivo = request.files["archivo"]
    try:
        cliente_syllabus = ClienteSyllabus()
        extraccion = cliente_syllabus.extraer_fechas_academicas(archivo.read())
        tareas_nuevas = construir_tareas_desde_extraccion(extraccion, curso)
        for tarea in tareas_nuevas:
            agregar_tarea(_ruta_repo_pendientes(), tarea)
        flash(
            f"Se agregaron {len(tareas_nuevas)} tareas desde el syllabus "
            f"({len(extraccion.get('parciales', []))} parciales, {len(extraccion.get('tareas', []))} entregas)."
        )
    except Exception as error:
        flash(f"No se pudo procesar el syllabus: {error}")
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
        detalles=request.form.get("detalles", ""),
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
    sesiones = _sesiones_ordenadas_con_indice()
    detalle_por_indice = {}
    for indice, sesion in sesiones:
        codigo_dsl = _extraer_codigo_dsl(sesion.notas)
        if codigo_dsl is not None:
            bloques = parsear_codigo_dsl(codigo_dsl)
            detalle_por_indice[indice] = {
                "bloques": bloques,
                "distancia_total": sum(bloque.repeticiones * bloque.distancia_m for bloque in bloques),
            }

    sugerencia = None
    if request.args.get("sugerir"):
        try:
            configuracion = _cargar_configuracion(RUTA_CONFIG_POR_DEFECTO)
            umbrales = configuracion.get("umbrales", {})
            estado_fisiologico = construir_estado_fisiologico(ClienteGarmin(), date.today())
            sugerencia = sugerir_parametros_sesion(
                estado_fisiologico,
                acwr_limite=umbrales.get("acwr_limite", 1.5),
                body_battery_bajo=umbrales.get("body_battery_bajo", 40),
                body_battery_medio=umbrales.get("body_battery_medio", 70),
            )
        except Exception as error:
            flash(f"No se pudo obtener una sugerencia con datos de Garmin: {error}")

    return render_template(
        "entrenamiento.html",
        sesiones=sesiones,
        detalle_por_indice=detalle_por_indice,
        nombre_archivo=nombre_archivo_plan_semana_actual(),
        sugerencia=sugerencia,
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


@app.route("/entrenamiento/generar-dsl", methods=["POST"])
def generar_sesion_desde_dsl():
    duracion = int(request.form["duracion"])
    try:
        cliente = ClienteSwimmingDSL()
        resultado = cliente.generar_sesion(
            objetivo=request.form["objetivo"],
            distancia=int(request.form["distancia"]),
            estilos=request.form.getlist("estilos"),
            duracion=duracion,
        )
        sesion_nueva = construir_sesion_desde_resultado(resultado, date.fromisoformat(request.form["fecha"]), duracion)
        agregar_sesion(_ruta_repo_entrenamiento(), sesion_nueva)
    except requests.exceptions.ConnectionError:
        flash("No se pudo conectar con el servidor de swimmingdsl. ¿Esta corriendo 'npm start' en server/?")
    except Exception as error:
        flash(f"No se pudo generar la sesion con swimmingdsl: {error}")
    return redirect(url_for("entrenamiento"))


@app.route("/entrenamiento/<int:indice>/enviar-a-garmin", methods=["POST"])
def enviar_sesion_a_garmin(indice: int):
    sesiones = cargar_plan_semana_actual(_ruta_repo_entrenamiento())
    sesion = sesiones[indice]
    codigo_dsl = _extraer_codigo_dsl(sesion.notas)
    if codigo_dsl is None:
        flash("Esta sesion no tiene codigo de swimmingdsl para enviar a Garmin.")
        return redirect(url_for("entrenamiento"))
    try:
        bloques = parsear_codigo_dsl(codigo_dsl)
        workout = construir_workout_natacion(f"Entrenamiento {sesion.fecha.isoformat()}", bloques)
        cliente_garmin = ClienteGarmin()
        respuesta_subida = cliente_garmin.subir_entrenamiento_natacion(workout)
        cliente_garmin.programar_entrenamiento(respuesta_subida["workoutId"], sesion.fecha)
        flash("Entrenamiento enviado y programado en Garmin correctamente.")
    except Exception as error:
        flash(f"No se pudo enviar el entrenamiento a Garmin: {error}")
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
