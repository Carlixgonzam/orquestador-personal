MARGEN_IZQUIERDO = 44
MARGEN = 16
ANCHO_POR_DEFECTO = 640
ALTO_POR_DEFECTO = 160


def _serie_numerica(filas: list[dict], campo: str) -> tuple[list[str], list[float]]:
    fechas = []
    valores = []
    for fila in filas:
        valor_texto = fila.get(campo)
        if valor_texto in (None, ""):
            continue
        fechas.append(fila["fecha"])
        valores.append(float(valor_texto))
    return fechas, valores


def _coordenadas(valores: list[float], ancho: int, alto: int) -> list[tuple[float, float]]:
    minimo = min(valores)
    maximo = max(valores)
    rango = (maximo - minimo) or 1
    ancho_util = ancho - MARGEN_IZQUIERDO - MARGEN
    alto_util = alto - 2 * MARGEN
    paso_x = ancho_util / max(len(valores) - 1, 1)

    coordenadas = []
    for indice, valor in enumerate(valores):
        x = MARGEN_IZQUIERDO + indice * paso_x
        y = MARGEN + alto_util - ((valor - minimo) / rango) * alto_util
        coordenadas.append((x, y))
    return coordenadas


def generar_svg_linea(
    fechas: list[str],
    valores: list[float],
    color: str = "#3d6a5c",
    ancho: int = ANCHO_POR_DEFECTO,
    alto: int = ALTO_POR_DEFECTO,
) -> str:
    if not valores:
        return '<p class="grafica-vacia">Todavia no hay suficientes datos.</p>'

    if len(valores) == 1:
        return f'<p class="grafica-vacia">Un solo dato hasta ahora ({fechas[0]}: {valores[0]:g}).</p>'

    coordenadas = _coordenadas(valores, ancho, alto)
    polilinea = " ".join(f"{x:.1f},{y:.1f}" for x, y in coordenadas)
    circulos = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3"></circle>' for x, y in coordenadas)

    return (
        f'<svg class="grafica-linea" viewBox="0 0 {ancho} {alto}" xmlns="http://www.w3.org/2000/svg" '
        f'style="--color-grafica: {color}">'
        f'<text x="{MARGEN_IZQUIERDO - 6}" y="{MARGEN + 4}" text-anchor="end" class="etiqueta-eje">{max(valores):g}</text>'
        f'<text x="{MARGEN_IZQUIERDO - 6}" y="{alto - MARGEN}" text-anchor="end" class="etiqueta-eje">{min(valores):g}</text>'
        f'<polyline points="{polilinea}" class="linea-grafica"></polyline>'
        f"{circulos}"
        f'<text x="{MARGEN_IZQUIERDO}" y="{alto - 2}" class="etiqueta-eje">{fechas[0]}</text>'
        f'<text x="{ancho - MARGEN}" y="{alto - 2}" text-anchor="end" class="etiqueta-eje">{fechas[-1]}</text>'
        f"</svg>"
    )


def generar_graficas_de_historial(filas: list[dict]) -> dict[str, str]:
    metricas = [
        ("Disposicion para entrenar", "training_readiness", "#3d6a5c"),
        ("Body battery", "body_battery", "#4a5a8c"),
        ("HRV (ms)", "hrv_valor_ms", "#8c4a6e"),
        ("ACWR", "acwr", "#b8862f"),
    ]
    graficas = {}
    for etiqueta, campo, color in metricas:
        fechas, valores = _serie_numerica(filas, campo)
        graficas[etiqueta] = generar_svg_linea(fechas, valores, color=color)
    return graficas
