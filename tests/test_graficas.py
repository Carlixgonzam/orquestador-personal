from interfaz.graficas import generar_graficas_de_historial, generar_svg_linea


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
