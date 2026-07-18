from datetime import date, timedelta

from fuentes.entrenamiento_cliente import obtener_sesion_de_hoy
from fuentes.horario_cliente import DIAS_SEMANA
from modelo.bloque_fijo import BloqueFijo
from modelo.sesion_entrenamiento import SesionEntrenamiento
from modelo.tarea import Tarea


def calcular_lunes_de_la_semana(fecha: date) -> date:
    return fecha - timedelta(days=fecha.weekday())


def construir_vista_semanal(
    lunes: date,
    bloques_fijos_por_dia: dict[str, list[BloqueFijo]],
    sesiones_semana: list[SesionEntrenamiento],
    tareas: list[Tarea],
) -> list[dict]:
    dias = []
    for indice, nombre_dia in enumerate(DIAS_SEMANA):
        fecha_dia = lunes + timedelta(days=indice)
        dias.append(
            {
                "dia_semana": nombre_dia,
                "fecha": fecha_dia,
                "bloques_fijos": bloques_fijos_por_dia.get(nombre_dia, []),
                "sesion_entrenamiento": obtener_sesion_de_hoy(sesiones_semana, fecha_dia),
                "tareas_del_dia": [tarea for tarea in tareas if tarea.fecha_limite == fecha_dia],
            }
        )
    return dias
