import json
from datetime import date

from fuentes.garmin_cliente import ClienteGarmin

RUTA_SALIDA_DIAGNOSTICO = "diagnostico_garmin.json"


def _claves_de_nivel_superior(datos):
    if isinstance(datos, dict):
        return list(datos.keys())
    if isinstance(datos, list) and datos and isinstance(datos[0], dict):
        return list(datos[0].keys())
    return type(datos).__name__


def _primer_elemento(lista, valor_por_defecto=None):
    return lista[0] if lista else valor_por_defecto


def _imprimir_json_compacto(etiqueta, datos) -> None:
    print(f"{etiqueta}:")
    print(json.dumps(datos, indent=2, ensure_ascii=False, default=str))
    print()


def main() -> None:
    cliente = ClienteGarmin()
    fecha_hoy = date.today()

    metricas = {
        "disposicion_entrenamiento": cliente.obtener_disposicion_entrenamiento(fecha_hoy),
        "hrv": cliente.obtener_hrv(fecha_hoy),
        "estado_entrenamiento": cliente.obtener_estado_entrenamiento(fecha_hoy),
        "metricas_maximas": cliente.obtener_metricas_maximas(fecha_hoy),
        "score_resistencia": cliente.obtener_score_resistencia(fecha_hoy),
        "frecuencia_cardiaca_reposo": cliente.obtener_frecuencia_cardiaca_reposo(fecha_hoy),
        "frecuencia_respiratoria": cliente.obtener_frecuencia_respiratoria(fecha_hoy),
        "estres": cliente.obtener_estres(fecha_hoy),
        "nivel_body_battery": cliente.obtener_nivel_body_battery(fecha_hoy),
    }

    with open(RUTA_SALIDA_DIAGNOSTICO, "w", encoding="utf-8") as archivo_salida:
        json.dump(metricas, archivo_salida, indent=2, ensure_ascii=False, default=str)

    print(f"JSON completo de cada metrica guardado en {RUTA_SALIDA_DIAGNOSTICO}")
    print()
    for nombre_metrica, datos in metricas.items():
        print(f"{nombre_metrica}: {_claves_de_nivel_superior(datos)}")
    print()

    print("--- detalle de los campos que usa el motor de decision ---")
    print()
    datos_hrv = metricas["hrv"] or {}
    datos_estado_entrenamiento = metricas["estado_entrenamiento"] or {}
    datos_frecuencia_reposo = metricas["frecuencia_cardiaca_reposo"] or {}
    _imprimir_json_compacto("disposicion_entrenamiento[0]", _primer_elemento(metricas["disposicion_entrenamiento"]))
    _imprimir_json_compacto("hrv.hrvSummary", datos_hrv.get("hrvSummary"))
    _imprimir_json_compacto("estado_entrenamiento.mostRecentTrainingLoadBalance", datos_estado_entrenamiento.get("mostRecentTrainingLoadBalance"))
    _imprimir_json_compacto("estado_entrenamiento.mostRecentTrainingStatus", datos_estado_entrenamiento.get("mostRecentTrainingStatus"))
    _imprimir_json_compacto("estado_entrenamiento.mostRecentVO2Max", datos_estado_entrenamiento.get("mostRecentVO2Max"))
    _imprimir_json_compacto("frecuencia_cardiaca_reposo.allMetrics", datos_frecuencia_reposo.get("allMetrics"))


if __name__ == "__main__":
    main()
