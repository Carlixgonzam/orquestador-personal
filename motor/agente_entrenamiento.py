from dataclasses import dataclass

from modelo.estado_fisiologico import EstadoFisiologico

ESTADOS_DE_RECUPERACION = {"overreaching", "detraining", "recovery"}

OBJETIVO_RECUPERACION = "recovery"
OBJETIVO_TECNICA = "technique"
OBJETIVO_RESISTENCIA = "endurance"
OBJETIVO_VELOCIDAD = "speed"

ESTILOS_BASICOS = ["freestyle"]
ESTILOS_VARIADOS = ["freestyle", "backstroke", "breaststroke", "butterfly"]


@dataclass
class SugerenciaEntrenamiento:
    objetivo: str
    distancia: int
    duracion: int
    estilos: list[str]
    justificacion: str


def sugerir_parametros_sesion(
    estado_fisiologico: EstadoFisiologico | None,
    acwr_limite: float = 1.5,
    body_battery_bajo: int = 40,
    body_battery_medio: int = 70,
) -> SugerenciaEntrenamiento:
    if estado_fisiologico is None:
        return SugerenciaEntrenamiento(
            OBJETIVO_RESISTENCIA,
            2000,
            45,
            ESTILOS_BASICOS,
            "Sin datos de Garmin disponibles hoy, se sugiere una sesion moderada por defecto",
        )

    if estado_fisiologico.training_status.lower() in ESTADOS_DE_RECUPERACION:
        return SugerenciaEntrenamiento(
            OBJETIVO_RECUPERACION,
            1500,
            35,
            ESTILOS_BASICOS,
            f"Estado de entrenamiento {estado_fisiologico.training_status}, se sugiere una sesion corta de recuperacion",
        )

    if estado_fisiologico.acwr is not None and estado_fisiologico.acwr > acwr_limite:
        return SugerenciaEntrenamiento(
            OBJETIVO_RECUPERACION,
            1500,
            35,
            ESTILOS_BASICOS,
            f"ACWR de {estado_fisiologico.acwr} por encima del limite configurado ({acwr_limite}), se sugiere recuperacion",
        )

    if estado_fisiologico.body_battery < body_battery_bajo:
        return SugerenciaEntrenamiento(
            OBJETIVO_TECNICA,
            1800,
            40,
            ESTILOS_VARIADOS,
            f"Body battery bajo ({estado_fisiologico.body_battery}), se sugiere una sesion de tecnica de baja intensidad",
        )

    if estado_fisiologico.body_battery < body_battery_medio:
        return SugerenciaEntrenamiento(
            OBJETIVO_RESISTENCIA,
            2500,
            60,
            ESTILOS_VARIADOS,
            f"Body battery moderado ({estado_fisiologico.body_battery}), se sugiere una sesion de resistencia aerobica",
        )

    return SugerenciaEntrenamiento(
        OBJETIVO_VELOCIDAD,
        2200,
        60,
        ESTILOS_VARIADOS,
        f"Body battery alto ({estado_fisiologico.body_battery}) y sin senales de sobrecarga, se sugiere una sesion de velocidad",
    )
