import os
from datetime import datetime

from fuentes.historial_cliente import cargar_historial, registrar_estado_fisiologico
from modelo.estado_fisiologico import EstadoFisiologico


def construir_estado(momento, body_battery=60, training_readiness=70):
    return EstadoFisiologico(
        momento=momento,
        training_readiness=training_readiness,
        training_status="productive",
        hrv_status="balanced",
        hrv_valor_ms=55.0,
        hrv_tendencia="estable",
        body_battery=body_battery,
        acwr=1.1,
    )


def test_cargar_historial_retorna_lista_vacia_si_no_existe_el_archivo(tmp_path):
    ruta_historial = str(tmp_path / "no_existe" / "historial.csv")
    assert cargar_historial(ruta_historial) == []


def test_registrar_estado_fisiologico_crea_el_archivo_con_una_fila(tmp_path):
    ruta_historial = str(tmp_path / "historial.csv")
    estado = construir_estado(datetime(2026, 8, 5, 10, 0))

    registrar_estado_fisiologico(ruta_historial, estado)

    assert os.path.exists(ruta_historial)
    filas = cargar_historial(ruta_historial)
    assert len(filas) == 1
    assert filas[0]["fecha"] == "2026-08-05"
    assert filas[0]["body_battery"] == "60"


def test_registrar_estado_fisiologico_actualiza_la_fila_del_mismo_dia_en_vez_de_duplicar(tmp_path):
    ruta_historial = str(tmp_path / "historial.csv")
    registrar_estado_fisiologico(ruta_historial, construir_estado(datetime(2026, 8, 5, 8, 0), body_battery=40))
    registrar_estado_fisiologico(ruta_historial, construir_estado(datetime(2026, 8, 5, 18, 0), body_battery=90))

    filas = cargar_historial(ruta_historial)
    assert len(filas) == 1
    assert filas[0]["body_battery"] == "90"


def test_registrar_estado_fisiologico_ordena_cronologicamente(tmp_path):
    ruta_historial = str(tmp_path / "historial.csv")
    registrar_estado_fisiologico(ruta_historial, construir_estado(datetime(2026, 8, 6, 8, 0)))
    registrar_estado_fisiologico(ruta_historial, construir_estado(datetime(2026, 8, 4, 8, 0)))
    registrar_estado_fisiologico(ruta_historial, construir_estado(datetime(2026, 8, 5, 8, 0)))

    filas = cargar_historial(ruta_historial)
    assert [fila["fecha"] for fila in filas] == ["2026-08-04", "2026-08-05", "2026-08-06"]
