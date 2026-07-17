from dataclasses import dataclass
from datetime import date


@dataclass
class SesionEntrenamiento:
    fecha: date
    tipo: str
    intensidad: str
    notas: str
