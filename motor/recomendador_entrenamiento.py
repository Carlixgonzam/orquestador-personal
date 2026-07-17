from dataclasses import dataclass

from modelo.sesion_entrenamiento import SesionEntrenamiento

ESTADOS_QUE_REQUIEREN_RECUPERACION = {"overreaching", "detraining"}

MANTENER = "mantener"
REDUCIR_INTENSIDAD = "reducir_intensidad"
RECUPERACION_ACTIVA = "recuperacion_activa"
SIN_SESION_PLANEADA = "sin_sesion_planeada"


@dataclass
class RecomendacionEntrenamiento:
    sesion_planeada: SesionEntrenamiento | None
    tipo_ajuste: str
    justificacion: str


def decidir_ajuste_entrenamiento(
    training_status: str,
    sesion_planeada_hoy: SesionEntrenamiento | None,
    acwr_alto: bool = False,
) -> RecomendacionEntrenamiento:
    if sesion_planeada_hoy is None:
        return RecomendacionEntrenamiento(
            None,
            SIN_SESION_PLANEADA,
            "No hay sesion de entrenamiento planeada para hoy",
        )

    if training_status.lower() in ESTADOS_QUE_REQUIEREN_RECUPERACION:
        return RecomendacionEntrenamiento(
            sesion_planeada_hoy,
            RECUPERACION_ACTIVA,
            f"El estado de entrenamiento es {training_status}, se reemplaza la sesion por recuperacion activa dentro del mismo bloque horario",
        )

    if acwr_alto:
        return RecomendacionEntrenamiento(
            sesion_planeada_hoy,
            REDUCIR_INTENSIDAD,
            "El ratio de carga aguda/cronica supera el limite configurado, se reduce la intensidad de la sesion planeada",
        )

    return RecomendacionEntrenamiento(
        sesion_planeada_hoy,
        MANTENER,
        "El estado fisiologico permite mantener la sesion planeada sin cambios",
    )
