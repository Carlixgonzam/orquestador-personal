from dataclasses import dataclass
from datetime import time


@dataclass(frozen=True)
class HuecoLibre:
    dia_semana: str
    hora_inicio: time
    hora_fin: time

    def duracion_minutos(self) -> int:
        minutos_inicio = self.hora_inicio.hour * 60 + self.hora_inicio.minute
        minutos_fin = self.hora_fin.hour * 60 + self.hora_fin.minute
        return minutos_fin - minutos_inicio
