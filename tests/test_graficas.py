from datetime import date

from interfaz.graficas import (
    calcular_fitness_fatiga_forma,
    generar_graficas_de_historial,
    generar_heatmap_entrenamientos,
    generar_svg_linea,
    generar_svg_pmc,
)
from modelo.sesion_entrenamiento import SesionEntrenamiento


def test_generar_svg_linea_sin_valores_muestra_mensaje_vacio():
    resultado = generar_svg_linea([], [])
    assert "Todavia no hay" in resultado
    assert "<svg" not in resultado


def test_generar_svg_linea_con_un_solo_valor_muestra_mensaje_con_el_dato():
    resultado = generar_svg_linea(["2026-07-17"], [45.0])
    assert "2026-07-17" in resultado
    assert "45" in resultado
    assert "<svg" not in resultado


def test_generar_svg_linea_con_varios_valores_genera_svg_valido():
    resultado = generar_svg_linea(["2026-07-13", "2026-07-14", "2026-07-15"], [70.0, 55.0, 45.0])

    assert "<svg" in resultado
    assert "polyline" in resultado
    assert resultado.count("<circle") == 3
    assert "2026-07-13" in resultado
    assert "2026-07-15" in resultado
    assert "70" in resultado
    assert "45" in resultado


def test_generar_svg_linea_usa_el_color_recibido():
    resultado = generar_svg_linea(["a", "b"], [1.0, 2.0], color="#123456")
    assert "#123456" in resultado


def test_generar_graficas_de_historial_produce_una_entrada_por_metrica():
    filas = [
        {"fecha": "2026-07-13", "training_readiness": "80", "body_battery": "70", "hrv_valor_ms": "60", "acwr": "1.0"},
        {"fecha": "2026-07-14", "training_readiness": "75", "body_battery": "65", "hrv_valor_ms": "58", "acwr": "1.1"},
    ]

    graficas = generar_graficas_de_historial(filas)

    assert set(graficas.keys()) == {"Disposicion para entrenar", "Body battery", "HRV (ms)", "ACWR"}
    assert "<svg" in graficas["Body battery"]


def test_generar_graficas_de_historial_ignora_valores_vacios_del_campo():
    filas = [
        {"fecha": "2026-07-13", "training_readiness": "80", "body_battery": "", "hrv_valor_ms": "60", "acwr": "1.0"},
        {"fecha": "2026-07-14", "training_readiness": "75", "body_battery": "65", "hrv_valor_ms": "58", "acwr": "1.1"},
    ]

    graficas = generar_graficas_de_historial(filas)

    assert "Todavia no hay" not in graficas["Disposicion para entrenar"]


def test_calcular_fitness_fatiga_forma_ignora_dias_sin_disposicion():
    filas = [
        {"fecha": "2026-07-13", "training_readiness": "80"},
        {"fecha": "2026-07-14", "training_readiness": ""},
        {"fecha": "2026-07-15", "training_readiness": "70"},
    ]

    fechas, fitness, fatiga, forma = calcular_fitness_fatiga_forma(filas)

    assert fechas == ["2026-07-13", "2026-07-15"]
    assert len(fitness) == len(fatiga) == len(forma) == 2


def test_calcular_fitness_fatiga_forma_fatiga_reacciona_mas_rapido_que_fitness():
    filas = [{"fecha": f"2026-07-{dia:02d}", "training_readiness": "40"} for dia in range(1, 15)]

    _, fitness, fatiga, _ = calcular_fitness_fatiga_forma(filas)

    assert fatiga[-1] > fitness[-1]


def test_calcular_fitness_fatiga_forma_dias_buenos_dan_forma_positiva():
    filas = [{"fecha": f"2026-07-{dia:02d}", "training_readiness": "20"} for dia in range(1, 20)]
    filas += [{"fecha": f"2026-08-{dia:02d}", "training_readiness": "90"} for dia in range(1, 26)]

    _, _, _, forma = calcular_fitness_fatiga_forma(filas)

    assert forma[-1] > 0


def test_generar_svg_pmc_sin_datos_muestra_mensaje_vacio():
    resultado = generar_svg_pmc([], [], [], [])
    assert "Todavia no hay" in resultado
    assert "<svg" not in resultado


def test_generar_svg_pmc_con_varios_dias_genera_las_tres_lineas():
    resultado = generar_svg_pmc(
        ["2026-07-13", "2026-07-14", "2026-07-15"],
        [1.0, 1.5, 2.0],
        [2.0, 1.0, 0.5],
        [-1.0, 0.5, 1.5],
    )

    assert resultado.count("<polyline") == 3
    assert "linea-pmc-fitness" in resultado
    assert "linea-pmc-fatiga" in resultado
    assert "linea-pmc-forma" in resultado


def test_generar_heatmap_entrenamientos_marca_nivel_alto_para_sesion_de_alta_intensidad():
    hoy = date(2026, 8, 3)
    sesiones = [SesionEntrenamiento(fecha=hoy, tipo="natacion", intensidad="alta", notas="")]

    resultado = generar_heatmap_entrenamientos(sesiones, hoy, numero_semanas=1)

    assert "heatmap-nivel-3" in resultado


def test_generar_heatmap_entrenamientos_trata_descanso_como_nivel_bajo():
    hoy = date(2026, 8, 3)
    sesiones = [SesionEntrenamiento(fecha=hoy, tipo="descanso", intensidad="baja", notas="")]

    resultado = generar_heatmap_entrenamientos(sesiones, hoy, numero_semanas=1)

    assert "heatmap-nivel-1" in resultado
    assert "heatmap-nivel-2" not in resultado
    assert "heatmap-nivel-3" not in resultado


def test_generar_heatmap_entrenamientos_dia_sin_sesion_es_nivel_cero():
    hoy = date(2026, 8, 3)

    resultado = generar_heatmap_entrenamientos([], hoy, numero_semanas=1)

    assert "heatmap-nivel-0" in resultado
    assert resultado.count("heatmap-celda") == 7
