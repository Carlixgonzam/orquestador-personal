import os
from datetime import date

import garminconnect
from dotenv import load_dotenv

RUTA_TOKEN_POR_DEFECTO = os.path.expanduser("~/.orquestador_personal/token_garmin")


def _fecha_texto(fecha: date | None) -> str:
    return (fecha or date.today()).isoformat()


class ClienteGarmin:
    def __init__(self, cliente_garmin=None, ruta_token: str = RUTA_TOKEN_POR_DEFECTO):
        self.ruta_token = ruta_token
        self.cliente_garmin = cliente_garmin or self._autenticar()

    def _autenticar(self):
        load_dotenv()
        correo = os.environ["GARMIN_EMAIL"]
        contrasena = os.environ["GARMIN_PASSWORD"]
        os.makedirs(os.path.dirname(self.ruta_token), exist_ok=True)
        cliente = garminconnect.Garmin(email=correo, password=contrasena)
        cliente.login(self.ruta_token)
        return cliente

    def obtener_disposicion_entrenamiento(self, fecha: date | None = None):
        return self.cliente_garmin.get_training_readiness(_fecha_texto(fecha))

    def obtener_hrv(self, fecha: date | None = None):
        return self.cliente_garmin.get_hrv_data(_fecha_texto(fecha))

    def obtener_estado_entrenamiento(self, fecha: date | None = None):
        return self.cliente_garmin.get_training_status(_fecha_texto(fecha))

    def obtener_metricas_maximas(self, fecha: date | None = None):
        return self.cliente_garmin.get_max_metrics(_fecha_texto(fecha))

    def obtener_score_resistencia(self, fecha: date | None = None):
        return self.cliente_garmin.get_endurance_score(_fecha_texto(fecha))

    def obtener_predicciones_carrera(self):
        return self.cliente_garmin.get_race_predictions()

    def obtener_frecuencia_cardiaca_reposo(self, fecha: date | None = None):
        return self.cliente_garmin.get_rhr_day(_fecha_texto(fecha))

    def obtener_frecuencia_respiratoria(self, fecha: date | None = None):
        return self.cliente_garmin.get_respiration_data(_fecha_texto(fecha))

    def obtener_estres(self, fecha: date | None = None):
        return self.cliente_garmin.get_stress_data(_fecha_texto(fecha))

    def obtener_eventos_body_battery(self, fecha: date | None = None):
        return self.cliente_garmin.get_body_battery_events(_fecha_texto(fecha))

    def obtener_nivel_body_battery(self, fecha: date | None = None):
        return self.cliente_garmin.get_body_battery(_fecha_texto(fecha))
