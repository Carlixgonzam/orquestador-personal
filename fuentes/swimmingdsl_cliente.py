import re
from dataclasses import dataclass
from datetime import date

import requests

from modelo.sesion_entrenamiento import SesionEntrenamiento

URL_BASE_POR_DEFECTO = "http://localhost:3000"

NOMBRES_DE_SECCION = {"warmup", "main", "cooldown"}

PATRON_REPETICION = re.compile(r"^(\d+)\s*x\s*(.+)$")
PATRON_DESCANSO = re.compile(r"^(.*?)\s+rest\s+(\d+)\s*s$")
PATRON_NADO = re.compile(
    r"^swim\s+(\d+)\s*m"
    r"(?:\s+(freestyle|backstroke|breaststroke|butterfly))?"
    r"(?:\s+(easy|moderate|hard))?"
    r"\s+pace\s+(\d+)"
)


@dataclass
class BloqueNado:
    seccion: str
    repeticiones: int
    distancia_m: int
    estilo: str | None
    intensidad: str | None
    pace_segundos: int
    descanso_segundos: int | None

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


def parsear_codigo_dsl(codigo: str) -> list[BloqueNado]:
    bloques = []
    seccion_actual = "main"
    for linea_cruda in codigo.splitlines():
        linea = linea_cruda.strip()
        if not linea or linea.startswith("session ") or linea == "}":
            continue
        primera_palabra = linea.split()[0]
        if primera_palabra in NOMBRES_DE_SECCION and linea.endswith("{"):
            seccion_actual = primera_palabra
            continue

        repeticiones = 1
        resto = linea
        coincidencia_repeticion = PATRON_REPETICION.match(linea)
        if coincidencia_repeticion:
            repeticiones = int(coincidencia_repeticion.group(1))
            resto = coincidencia_repeticion.group(2)

        descanso_segundos = None
        coincidencia_descanso = PATRON_DESCANSO.match(resto)
        if coincidencia_descanso:
            resto = coincidencia_descanso.group(1)
            descanso_segundos = int(coincidencia_descanso.group(2))

        coincidencia_nado = PATRON_NADO.match(resto)
        if not coincidencia_nado:
            continue

        bloques.append(
            BloqueNado(
                seccion=seccion_actual,
                repeticiones=repeticiones,
                distancia_m=int(coincidencia_nado.group(1)),
                estilo=coincidencia_nado.group(2),
                intensidad=coincidencia_nado.group(3),
                pace_segundos=int(coincidencia_nado.group(4)),
                descanso_segundos=descanso_segundos,
            )
        )
    return bloques
