import os
from datetime import date, datetime

import yaml

from fuentes.entrenamiento_cliente import cargar_plan_semana_actual, obtener_sesion_de_hoy
from fuentes.garmin_cliente import ClienteGarmin
from fuentes.horario_cliente import calcular_huecos_libres, cargar_bloques_fijos, nombre_dia_semana
from fuentes.pendientes_cliente import cargar_tareas_pendientes
from modelo.estado_fisiologico import EstadoFisiologico
from motor.priorizador import HorarioHoy, decidir_hoy
from salida.generador_reporte import generar_reporte

RAIZ_DEL_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_CONFIG_POR_DEFECTO = os.path.join(RAIZ_DEL_PROYECTO, "config", "config.yaml")
RUTA_SALIDA_POR_DEFECTO = os.path.join(RAIZ_DEL_PROYECTO, "hoy.md")


def _cargar_configuracion(ruta_config: str) -> dict:
    with open(ruta_config, encoding="utf-8") as archivo_config:
        return yaml.safe_load(archivo_config)


def _primer_elemento(lista, valor_por_defecto=None):
    return lista[0] if lista else valor_por_defecto


def _extraer_clasificacion_entrenamiento(datos_estado_entrenamiento: dict) -> str:
    valores_por_fecha = datos_estado_entrenamiento.get("mostRecentTrainingStatus", {}).get(
        "latestTrainingStatusData", {}
    )
    if not valores_por_fecha:
        return "desconocido"
    primer_valor = next(iter(valores_por_fecha.values()))
    return primer_valor.get("trainingStatus", "desconocido")


def _extraer_acwr(datos_estado_entrenamiento: dict) -> float | None:
    balance_de_carga = datos_estado_entrenamiento.get("mostRecentTrainingLoadBalance", {})
    porcentaje = balance_de_carga.get("acwrPercent")
    return porcentaje / 100 if porcentaje is not None else None


def _extraer_frecuencia_cardiaca_reposo(datos_rhr: dict) -> int | None:
    metricas = datos_rhr.get("allMetrics", {}).get("metricsMap", {})
    valores = metricas.get("WELLNESS_RESTING_HEART_RATE", [])
    return _primer_elemento(valores, {}).get("value")


def _extraer_nivel_body_battery(datos_body_battery: list) -> int:
    return _primer_elemento(datos_body_battery, {}).get("charged", 0)


def construir_estado_fisiologico(cliente_garmin: ClienteGarmin, fecha: date) -> EstadoFisiologico:
    disposicion = _primer_elemento(cliente_garmin.obtener_disposicion_entrenamiento(fecha), {})
    resumen_hrv = (cliente_garmin.obtener_hrv(fecha) or {}).get("hrvSummary", {})
    datos_estado_entrenamiento = cliente_garmin.obtener_estado_entrenamiento(fecha)
    metricas_maximas = _primer_elemento(cliente_garmin.obtener_metricas_maximas(fecha), {})
    datos_score_resistencia = cliente_garmin.obtener_score_resistencia(fecha) or {}
    datos_predicciones = cliente_garmin.obtener_predicciones_carrera() or {}
    datos_frecuencia_respiratoria = cliente_garmin.obtener_frecuencia_respiratoria(fecha) or {}
    datos_estres = cliente_garmin.obtener_estres(fecha) or {}
    eventos_body_battery = cliente_garmin.obtener_eventos_body_battery(fecha) or []
    datos_nivel_body_battery = cliente_garmin.obtener_nivel_body_battery(fecha) or []

    return EstadoFisiologico(
        momento=datetime.combine(fecha, datetime.now().time()),
        training_readiness=disposicion.get("score", 0),
        training_status=_extraer_clasificacion_entrenamiento(datos_estado_entrenamiento),
        hrv_status=resumen_hrv.get("status", "desconocido"),
        hrv_valor_ms=resumen_hrv.get("lastNightAvg"),
        hrv_tendencia=resumen_hrv.get("status"),
        body_battery=_extraer_nivel_body_battery(datos_nivel_body_battery),
        eventos_body_battery=eventos_body_battery,
        vo2_max=metricas_maximas.get("generic", {}).get("vo2MaxValue"),
        endurance_score=datos_score_resistencia.get("overallScore"),
        predicciones_carrera=datos_predicciones,
        frecuencia_cardiaca_reposo=_extraer_frecuencia_cardiaca_reposo(
            cliente_garmin.obtener_frecuencia_cardiaca_reposo(fecha)
        ),
        frecuencia_respiratoria=datos_frecuencia_respiratoria.get("avgWakingRespirationValue"),
        estres_promedio=datos_estres.get("avgStressLevel"),
        acwr=_extraer_acwr(datos_estado_entrenamiento),
    )


def construir_horario_hoy(ruta_config: str, fecha: date) -> HorarioHoy:
    bloques_fijos = cargar_bloques_fijos(ruta_config)
    dia_semana = nombre_dia_semana(fecha)
    bloques_fijos_de_hoy = [bloque for bloque in bloques_fijos if bloque.dia_semana == dia_semana]
    huecos_libres = calcular_huecos_libres(dia_semana, bloques_fijos)
    return HorarioHoy(dia_semana, bloques_fijos_de_hoy, huecos_libres)


def ejecutar(
    fecha: date | None = None,
    ruta_config: str = RUTA_CONFIG_POR_DEFECTO,
    ruta_salida: str = RUTA_SALIDA_POR_DEFECTO,
    cliente_garmin: ClienteGarmin | None = None,
) -> str:
    fecha_referencia = fecha or date.today()
    configuracion = _cargar_configuracion(ruta_config)
    umbrales = configuracion.get("umbrales", {})
    rutas_repos = configuracion.get("rutas_repos", {})

    horario_hoy = construir_horario_hoy(ruta_config, fecha_referencia)

    cliente_garmin = cliente_garmin or ClienteGarmin()
    estado_fisiologico = construir_estado_fisiologico(cliente_garmin, fecha_referencia)

    tareas_pendientes = cargar_tareas_pendientes(rutas_repos["pendientes"])

    sesiones_semana = cargar_plan_semana_actual(rutas_repos["entrenamiento"], fecha_referencia)
    sesion_planeada_hoy = obtener_sesion_de_hoy(sesiones_semana, fecha_referencia)

    resultado = decidir_hoy(
        estado_fisiologico,
        tareas_pendientes,
        horario_hoy,
        sesion_planeada_hoy=sesion_planeada_hoy,
        acwr_limite=umbrales.get("acwr_limite", 1.5),
        body_battery_bajo=umbrales.get("body_battery_bajo", 40),
        body_battery_medio=umbrales.get("body_battery_medio", 70),
    )

    return generar_reporte(resultado, estado_fisiologico, horario_hoy, ruta_salida=ruta_salida)


if __name__ == "__main__":
    ruta_generada = ejecutar()
    print(f"Reporte generado en {ruta_generada}")
