from datetime import date

import requests

from modelo.sesion_entrenamiento import SesionEntrenamiento

URL_BASE_POR_DEFECTO = "http://localhost:3000"

MAPEO_INTENSIDAD_POR_OBJETIVO = {
    "speed": "alta",
    "endurance": "moderada",
    "technique": "baja",
    "recovery": "baja",
}


class ClienteSwimmingDSL:
    def __init__(self, url_base: str = URL_BASE_POR_DEFECTO):
        self.url_base = url_base

    def generar_sesion(self, objetivo: str, distancia: int, estilos: list[str], duracion: int) -> dict:
        respuesta = requests.post(
            f"{self.url_base}/api/generate",
            json={"goal": objetivo, "distance": distancia, "styles": estilos, "duration": duracion},
            timeout=35,
        )
        respuesta.raise_for_status()
        resultado = respuesta.json()
        if not resultado.get("success"):
            raise RuntimeError(resultado.get("error", "swimmingdsl no pudo generar la sesion"))
        return resultado


def construir_sesion_desde_resultado(resultado: dict, fecha: date, duracion: int) -> SesionEntrenamiento:
    objetivo = resultado["goal"]
    intensidad = MAPEO_INTENSIDAD_POR_OBJETIVO.get(objetivo, "moderada")
    notas = f"Generado por swimmingdsl ({objetivo}, {resultado['distance']}m, {duracion}min):\n{resultado['code']}"
    return SesionEntrenamiento(fecha=fecha, tipo="natacion", intensidad=intensidad, notas=notas)
