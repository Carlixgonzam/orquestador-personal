from dataclasses import dataclass
from datetime import date


@dataclass
class Tarea:
    curso: str
    titulo: str
    fecha_limite: date
    energia_requerida: str
    peso_academico: float
    estado: str
    detalles: str = ""
