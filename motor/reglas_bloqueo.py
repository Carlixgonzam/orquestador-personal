from datetime import datetime, time

from fuentes.horario_cliente import nombre_dia_semana
from modelo.bloque_fijo import BloqueFijo
from modelo.estado_fisiologico import EstadoFisiologico

ESTADOS_DE_SOBREENTRENAMIENTO = {"overreaching", "detraining"}
DIAS_CON_ENTRENAMIENTO_MATUTINO = {"lunes", "martes", "jueves"}
HORA_LIMITE_ENTRENAMIENTO_MATUTINO = time(9, 0)


def hay_bloque_fijo_activo(momento: datetime, bloques_fijos: list[BloqueFijo]) -> BloqueFijo | None:
    dia_semana = nombre_dia_semana(momento)
    hora_actual = momento.time()
    for bloque in bloques_fijos:
        if bloque.dia_semana == dia_semana and bloque.hora_inicio <= hora_actual < bloque.hora_fin:
            return bloque
    return None


def hay_sobreentrenamiento(estado_fisiologico: EstadoFisiologico) -> bool:
    return estado_fisiologico.training_status.lower() in ESTADOS_DE_SOBREENTRENAMIENTO


def hay_acwr_alto(estado_fisiologico: EstadoFisiologico, acwr_limite: float) -> bool:
    if estado_fisiologico.acwr is None:
        return False
    return estado_fisiologico.acwr > acwr_limite


def es_ventana_entrenamiento_matutino(momento: datetime) -> bool:
    dia_semana = nombre_dia_semana(momento)
    if dia_semana not in DIAS_CON_ENTRENAMIENTO_MATUTINO:
        return False
    return momento.time() < HORA_LIMITE_ENTRENAMIENTO_MATUTINO


def hay_hrv_desbalanceado_con_bateria_baja(
    estado_fisiologico: EstadoFisiologico,
    momento: datetime,
    body_battery_bajo: int,
) -> bool:
    if es_ventana_entrenamiento_matutino(momento):
        return False
    hrv_desbalanceado = estado_fisiologico.hrv_status.lower() == "unbalanced"
    bateria_baja = estado_fisiologico.body_battery < body_battery_bajo
    return hrv_desbalanceado and bateria_baja
