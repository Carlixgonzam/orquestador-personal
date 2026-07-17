from datetime import datetime, time

import yaml

from modelo.bloque_fijo import BloqueFijo
from modelo.hueco_libre import HuecoLibre

DIAS_SEMANA = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
INICIO_DIA = time(0, 0)
FIN_DIA = time(23, 59)


def nombre_dia_semana(momento: datetime) -> str:
    return DIAS_SEMANA[momento.weekday()]


def _hora_desde_texto(texto: str) -> time:
    horas, minutos = texto.split(":")
    return time(int(horas), int(minutos))


def cargar_bloques_fijos(ruta_config: str) -> list[BloqueFijo]:
    with open(ruta_config, encoding="utf-8") as archivo_config:
        contenido = yaml.safe_load(archivo_config)

    bloques_crudos = contenido.get("bloques_fijos", [])
    return [
        BloqueFijo(
            dia_semana=bloque["dia_semana"],
            hora_inicio=_hora_desde_texto(bloque["hora_inicio"]),
            hora_fin=_hora_desde_texto(bloque["hora_fin"]),
            tipo=bloque["tipo"],
            nombre=bloque["nombre"],
            codigo=bloque.get("codigo"),
        )
        for bloque in bloques_crudos
    ]


def bloque_fijo_activo(momento: datetime, bloques_fijos: list[BloqueFijo]) -> BloqueFijo | None:
    dia_semana = nombre_dia_semana(momento)
    hora_actual = momento.time()
    for bloque in bloques_fijos:
        if bloque.dia_semana != dia_semana:
            continue
        if bloque.hora_inicio <= hora_actual < bloque.hora_fin:
            return bloque
    return None


def calcular_huecos_libres(dia_semana: str, bloques_fijos: list[BloqueFijo]) -> list[HuecoLibre]:
    bloques_del_dia = sorted(
        (bloque for bloque in bloques_fijos if bloque.dia_semana == dia_semana),
        key=lambda bloque: bloque.hora_inicio,
    )

    huecos = []
    cursor = INICIO_DIA
    for bloque in bloques_del_dia:
        if bloque.hora_inicio > cursor:
            huecos.append(HuecoLibre(dia_semana, cursor, bloque.hora_inicio))
        if bloque.hora_fin > cursor:
            cursor = bloque.hora_fin

    if cursor < FIN_DIA:
        huecos.append(HuecoLibre(dia_semana, cursor, FIN_DIA))

    return huecos
