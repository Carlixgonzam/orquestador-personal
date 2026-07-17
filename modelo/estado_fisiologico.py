from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class EstadoFisiologico:
    momento: datetime
    training_readiness: int
    training_status: str
    hrv_status: str
    hrv_valor_ms: float | None
    hrv_tendencia: str | None
    body_battery: int
    eventos_body_battery: list[dict] = field(default_factory=list)
    vo2_max: float | None = None
    endurance_score: float | None = None
    predicciones_carrera: dict = field(default_factory=dict)
    frecuencia_cardiaca_reposo: int | None = None
    frecuencia_respiratoria: float | None = None
    estres_promedio: int | None = None
    acwr: float | None = None
