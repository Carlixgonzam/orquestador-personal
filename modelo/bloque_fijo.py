from dataclasses import dataclass
from datetime import time


@dataclass(frozen=True)
class BloqueFijo:
    dia_semana: str
    hora_inicio: time
    hora_fin: time
    tipo: str
    nombre: str
    codigo: str | None = None
