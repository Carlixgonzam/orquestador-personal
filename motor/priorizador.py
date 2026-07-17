from dataclasses import dataclass
from datetime import datetime

from modelo.bloque_fijo import BloqueFijo
from modelo.estado_fisiologico import EstadoFisiologico
from modelo.hueco_libre import HuecoLibre
from modelo.sesion_entrenamiento import SesionEntrenamiento
from modelo.tarea import Tarea
from motor import reglas_bloqueo
from motor.recomendador_entrenamiento import RecomendacionEntrenamiento, decidir_ajuste_entrenamiento

NIVEL_ENERGIA_ALTA = "alta"
NIVEL_ENERGIA_MEDIA = "media"
NIVEL_ENERGIA_BAJA = "baja"


@dataclass
class HorarioHoy:
    dia_semana: str
    bloques_fijos: list[BloqueFijo]
    huecos_libres: list[HuecoLibre]


@dataclass
class AsignacionHueco:
    hueco: HuecoLibre
    tarea: Tarea | None


@dataclass
class ResultadoPriorizacion:
    bloque_fijo_activo: BloqueFijo | None
    asignaciones: list[AsignacionHueco]
    recomendacion_entrenamiento: RecomendacionEntrenamiento | None
    alertas: list[str]


def _ordenar_tareas(tareas: list[Tarea]) -> list[Tarea]:
    return sorted(tareas, key=lambda tarea: (tarea.fecha_limite, -tarea.peso_academico))


def _tareas_por_nivel_energia(tareas_pendientes: list[Tarea], nivel_energia: str) -> list[Tarea]:
    return [tarea for tarea in tareas_pendientes if tarea.energia_requerida == nivel_energia]


def _nivel_energia_por_body_battery(body_battery: int, body_battery_bajo: int, body_battery_medio: int) -> str:
    if body_battery < body_battery_bajo:
        return NIVEL_ENERGIA_BAJA
    if body_battery < body_battery_medio:
        return NIVEL_ENERGIA_MEDIA
    return NIVEL_ENERGIA_ALTA


def _repartir_tareas_en_huecos(tareas_ordenadas: list[Tarea], huecos_libres: list[HuecoLibre]) -> list[AsignacionHueco]:
    tareas_restantes = list(tareas_ordenadas)
    asignaciones = []
    for hueco in huecos_libres:
        tarea_asignada = tareas_restantes.pop(0) if tareas_restantes else None
        asignaciones.append(AsignacionHueco(hueco, tarea_asignada))
    return asignaciones


def decidir_hoy(
    estado_fisiologico: EstadoFisiologico,
    tareas_pendientes: list[Tarea],
    horario_hoy: HorarioHoy,
    sesion_planeada_hoy: SesionEntrenamiento | None = None,
    acwr_limite: float = 1.5,
    body_battery_bajo: int = 40,
    body_battery_medio: int = 70,
) -> ResultadoPriorizacion:
    momento = estado_fisiologico.momento

    bloque_activo = reglas_bloqueo.hay_bloque_fijo_activo(momento, horario_hoy.bloques_fijos)
    if bloque_activo is not None:
        return ResultadoPriorizacion(bloque_activo, [], None, [])

    acwr_alto = reglas_bloqueo.hay_acwr_alto(estado_fisiologico, acwr_limite)
    recomendacion_entrenamiento = decidir_ajuste_entrenamiento(
        estado_fisiologico.training_status, sesion_planeada_hoy, acwr_alto
    )

    if reglas_bloqueo.hay_sobreentrenamiento(estado_fisiologico):
        alertas = [
            f"Estado de entrenamiento en {estado_fisiologico.training_status}: "
            "solo se recomiendan tareas de carga baja, sin entrenamiento adicional fuera del plan fijo"
        ]
        tareas_candidatas = _ordenar_tareas(_tareas_por_nivel_energia(tareas_pendientes, NIVEL_ENERGIA_BAJA))
        asignaciones = _repartir_tareas_en_huecos(tareas_candidatas, horario_hoy.huecos_libres)
        return ResultadoPriorizacion(None, asignaciones, recomendacion_entrenamiento, alertas)

    if acwr_alto:
        alertas = [
            f"ACWR por encima del limite configurado ({acwr_limite}): "
            "se reduce la intensidad de la proxima sesion y se prioriza lo academico"
        ]
        tareas_candidatas = _ordenar_tareas(tareas_pendientes)
        asignaciones = _repartir_tareas_en_huecos(tareas_candidatas, horario_hoy.huecos_libres)
        return ResultadoPriorizacion(None, asignaciones, recomendacion_entrenamiento, alertas)

    if reglas_bloqueo.hay_hrv_desbalanceado_con_bateria_baja(estado_fisiologico, momento, body_battery_bajo):
        alertas = ["HRV desbalanceado con body battery bajo: dia de carga baja, solo tareas administrativas"]
        tareas_candidatas = _ordenar_tareas(_tareas_por_nivel_energia(tareas_pendientes, NIVEL_ENERGIA_BAJA))
        asignaciones = _repartir_tareas_en_huecos(tareas_candidatas, horario_hoy.huecos_libres)
        return ResultadoPriorizacion(None, asignaciones, recomendacion_entrenamiento, alertas)

    nivel_energia = _nivel_energia_por_body_battery(
        estado_fisiologico.body_battery, body_battery_bajo, body_battery_medio
    )
    tareas_candidatas = _ordenar_tareas(_tareas_por_nivel_energia(tareas_pendientes, nivel_energia))
    asignaciones = _repartir_tareas_en_huecos(tareas_candidatas, horario_hoy.huecos_libres)
    return ResultadoPriorizacion(None, asignaciones, recomendacion_entrenamiento, [])


def decidir_hoy_sin_garmin(
    tareas_pendientes: list[Tarea],
    horario_hoy: HorarioHoy,
    momento: datetime,
    sesion_planeada_hoy: SesionEntrenamiento | None = None,
) -> ResultadoPriorizacion:
    bloque_activo = reglas_bloqueo.hay_bloque_fijo_activo(momento, horario_hoy.bloques_fijos)
    if bloque_activo is not None:
        return ResultadoPriorizacion(bloque_activo, [], None, [])

    alertas = ["Garmin no disponible: mostrando tareas academicas por deadline, sin ajuste fisiologico"]
    recomendacion_entrenamiento = decidir_ajuste_entrenamiento("desconocido", sesion_planeada_hoy, acwr_alto=False)
    tareas_candidatas = _ordenar_tareas(tareas_pendientes)
    asignaciones = _repartir_tareas_en_huecos(tareas_candidatas, horario_hoy.huecos_libres)
    return ResultadoPriorizacion(None, asignaciones, recomendacion_entrenamiento, alertas)
