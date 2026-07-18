import json
import os
from dataclasses import asdict
from datetime import date, datetime, time

from modelo.estado_fisiologico import EstadoFisiologico
from motor.priorizador import HorarioHoy, ResultadoPriorizacion


def _serializar_valores_no_nativos(valor):
    if isinstance(valor, (datetime, date, time)):
        return valor.isoformat()
    raise TypeError(f"No se puede serializar el valor {valor!r} de tipo {type(valor)}")


def guardar_snapshot_diario(
    ruta_snapshot: str,
    resultado: ResultadoPriorizacion,
    estado_fisiologico: EstadoFisiologico | None,
    horario_hoy: HorarioHoy,
    nombres_cursos: dict[str, str],
    fecha: date,
) -> None:
    contenido = {
        "fecha": fecha.isoformat(),
        "dia_semana": horario_hoy.dia_semana,
        "nombres_cursos": nombres_cursos,
        "bloques_fijos_hoy": [asdict(bloque) for bloque in horario_hoy.bloques_fijos],
        "resultado": asdict(resultado),
        "estado_fisiologico": asdict(estado_fisiologico) if estado_fisiologico else None,
    }
    os.makedirs(os.path.dirname(ruta_snapshot) or ".", exist_ok=True)
    with open(ruta_snapshot, "w", encoding="utf-8") as archivo_snapshot:
        json.dump(contenido, archivo_snapshot, default=_serializar_valores_no_nativos, ensure_ascii=False, indent=2)


def cargar_snapshot_diario(ruta_snapshot: str) -> dict | None:
    if not os.path.exists(ruta_snapshot):
        return None
    with open(ruta_snapshot, encoding="utf-8") as archivo_snapshot:
        return json.load(archivo_snapshot)
