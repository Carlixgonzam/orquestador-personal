import csv
import os

from modelo.estado_fisiologico import EstadoFisiologico

NOMBRES_CAMPOS_HISTORIAL = [
    "fecha",
    "training_readiness",
    "training_status",
    "hrv_status",
    "hrv_valor_ms",
    "body_battery",
    "acwr",
    "frecuencia_cardiaca_reposo",
    "frecuencia_respiratoria",
    "estres_promedio",
    "vo2_max",
    "endurance_score",
]


def _fila_desde_estado(estado_fisiologico: EstadoFisiologico) -> dict:
    return {
        "fecha": estado_fisiologico.momento.date().isoformat(),
        "training_readiness": estado_fisiologico.training_readiness,
        "training_status": estado_fisiologico.training_status,
        "hrv_status": estado_fisiologico.hrv_status,
        "hrv_valor_ms": estado_fisiologico.hrv_valor_ms,
        "body_battery": estado_fisiologico.body_battery,
        "acwr": estado_fisiologico.acwr,
        "frecuencia_cardiaca_reposo": estado_fisiologico.frecuencia_cardiaca_reposo,
        "frecuencia_respiratoria": estado_fisiologico.frecuencia_respiratoria,
        "estres_promedio": estado_fisiologico.estres_promedio,
        "vo2_max": estado_fisiologico.vo2_max,
        "endurance_score": estado_fisiologico.endurance_score,
    }


def cargar_historial(ruta_historial: str) -> list[dict]:
    if not os.path.exists(ruta_historial):
        return []
    with open(ruta_historial, encoding="utf-8", newline="") as archivo_historial:
        return list(csv.DictReader(archivo_historial))


def guardar_historial(ruta_historial: str, filas: list[dict]) -> None:
    os.makedirs(os.path.dirname(ruta_historial), exist_ok=True)
    with open(ruta_historial, "w", encoding="utf-8", newline="") as archivo_historial:
        escritor = csv.DictWriter(archivo_historial, fieldnames=NOMBRES_CAMPOS_HISTORIAL)
        escritor.writeheader()
        escritor.writerows(filas)


def registrar_estado_fisiologico(ruta_historial: str, estado_fisiologico: EstadoFisiologico) -> None:
    filas = cargar_historial(ruta_historial)
    fila_nueva = _fila_desde_estado(estado_fisiologico)
    filas = [fila for fila in filas if fila["fecha"] != fila_nueva["fecha"]]
    filas.append(fila_nueva)
    filas.sort(key=lambda fila: fila["fecha"])
    guardar_historial(ruta_historial, filas)
