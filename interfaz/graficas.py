import html
from datetime import date, timedelta

MARGEN_IZQUIERDO = 44
MARGEN = 16
ANCHO_POR_DEFECTO = 640
ALTO_POR_DEFECTO = 160

DIAS_CTL = 42
DIAS_ATL = 7
NUMERO_SEMANAS_HEATMAP = 12
ORDEN_INTENSIDAD = {"baja": 1, "moderada": 2, "alta": 3}
DIAS_ABREVIADOS = ["L", "M", "X", "J", "V", "S", "D"]


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


def calcular_fitness_fatiga_forma(filas: list[dict]) -> tuple[list[str], list[float], list[float], list[float]]:
    fechas, disposiciones = _serie_numerica(filas, "training_readiness")
    cargas = [100.0 - disposicion for disposicion in disposiciones]

    fitness = []
    fatiga = []
    forma = []
    ctl = 0.0
    atl = 0.0
    for carga in cargas:
        ctl += (carga - ctl) / DIAS_CTL
        atl += (carga - atl) / DIAS_ATL
        fitness.append(ctl)
        fatiga.append(atl)
        forma.append(ctl - atl)
    return fechas, fitness, fatiga, forma


def generar_svg_pmc(
    fechas: list[str],
    fitness: list[float],
    fatiga: list[float],
    forma: list[float],
    ancho: int = ANCHO_POR_DEFECTO,
    alto: int = ALTO_POR_DEFECTO,
) -> str:
    if not fitness:
        return '<p class="grafica-vacia">Todavia no hay suficientes datos.</p>'
    if len(fitness) == 1:
        return '<p class="grafica-vacia">Un solo dato hasta ahora, hacen falta mas dias para ver la tendencia.</p>'

    todos_los_valores = fitness + fatiga + forma
    minimo = min(todos_los_valores)
    maximo = max(todos_los_valores)
    rango = (maximo - minimo) or 1
    ancho_util = ancho - MARGEN_IZQUIERDO - MARGEN
    alto_util = alto - 2 * MARGEN
    paso_x = ancho_util / max(len(fitness) - 1, 1)

    def _puntos(serie: list[float]) -> str:
        coordenadas = []
        for indice, valor in enumerate(serie):
            x = MARGEN_IZQUIERDO + indice * paso_x
            y = MARGEN + alto_util - ((valor - minimo) / rango) * alto_util
            coordenadas.append(f"{x:.1f},{y:.1f}")
        return " ".join(coordenadas)

    x_hoy = MARGEN_IZQUIERDO + (len(fitness) - 1) * paso_x

    return (
        f'<svg class="grafica-linea grafica-pmc" viewBox="0 0 {ancho} {alto}" xmlns="http://www.w3.org/2000/svg">'
        f'<line x1="{x_hoy:.1f}" y1="{MARGEN}" x2="{x_hoy:.1f}" y2="{alto - MARGEN}" class="linea-marcador-hoy"></line>'
        f'<text x="{x_hoy:.1f}" y="{MARGEN - 4}" text-anchor="middle" class="etiqueta-eje etiqueta-marcador-hoy">HOY</text>'
        f'<polyline points="{_puntos(fitness)}" class="linea-pmc linea-pmc-fitness"></polyline>'
        f'<polyline points="{_puntos(fatiga)}" class="linea-pmc linea-pmc-fatiga"></polyline>'
        f'<polyline points="{_puntos(forma)}" class="linea-pmc linea-pmc-forma"></polyline>'
        f'<text x="{MARGEN_IZQUIERDO}" y="{alto - 2}" class="etiqueta-eje">{fechas[0]}</text>'
        f'<text x="{ancho - MARGEN}" y="{alto - 2}" text-anchor="end" class="etiqueta-eje">{fechas[-1]}</text>'
        f"</svg>"
    )


def _nivel_del_dia(sesiones_del_dia: list) -> int:
    if not sesiones_del_dia:
        return 0
    niveles = [ORDEN_INTENSIDAD.get(sesion.intensidad, 1) for sesion in sesiones_del_dia if sesion.tipo != "descanso"]
    if not niveles:
        return 1
    return max(niveles)


def _describir_dia(fecha_dia: date, sesiones_del_dia: list) -> str:
    if not sesiones_del_dia:
        return fecha_dia.isoformat()
    resumen = ", ".join(f"{sesion.tipo} ({sesion.intensidad})" for sesion in sesiones_del_dia)
    return f"{fecha_dia.isoformat()}: {resumen}"


def generar_heatmap_entrenamientos(sesiones: list, hoy: date, numero_semanas: int = NUMERO_SEMANAS_HEATMAP) -> str:
    lunes_semana_actual = hoy - timedelta(days=hoy.weekday())
    lunes_inicio = lunes_semana_actual - timedelta(weeks=numero_semanas - 1)

    sesiones_por_fecha: dict[date, list] = {}
    for sesion in sesiones:
        sesiones_por_fecha.setdefault(sesion.fecha, []).append(sesion)

    columnas = []
    for indice_semana in range(numero_semanas):
        lunes_de_esta_semana = lunes_inicio + timedelta(weeks=indice_semana)
        celdas = []
        for offset_dia in range(7):
            fecha_dia = lunes_de_esta_semana + timedelta(days=offset_dia)
            sesiones_del_dia = sesiones_por_fecha.get(fecha_dia, [])
            nivel = _nivel_del_dia(sesiones_del_dia)
            titulo = html.escape(_describir_dia(fecha_dia, sesiones_del_dia))
            celdas.append(f'<div class="heatmap-celda heatmap-nivel-{nivel}" title="{titulo}"></div>')
        columnas.append(f'<div class="heatmap-columna">{"".join(celdas)}</div>')

    encabezado_dias = "".join(f'<span class="heatmap-dia-nombre">{nombre}</span>' for nombre in DIAS_ABREVIADOS)
    leyenda = (
        '<div class="heatmap-leyenda">'
        "<span>Menos</span>"
        '<span class="heatmap-leyenda-celdas">'
        '<span class="heatmap-leyenda-punto heatmap-nivel-0"></span>'
        '<span class="heatmap-leyenda-punto heatmap-nivel-1"></span>'
        '<span class="heatmap-leyenda-punto heatmap-nivel-2"></span>'
        '<span class="heatmap-leyenda-punto heatmap-nivel-3"></span>'
        "</span>"
        "<span>Mas</span>"
        "</div>"
    )

    return (
        '<div class="heatmap-envoltorio">'
        '<div class="heatmap-fila">'
        f'<div class="heatmap-cabecera-dias">{encabezado_dias}</div>'
        f'<div class="heatmap-entrenamientos">{"".join(columnas)}</div>'
        "</div>"
        f"{leyenda}"
        "</div>"
    )


def generar_graficas_de_historial(filas: list[dict]) -> dict[str, str]:
    metricas = [
        ("Disposicion para entrenar", "training_readiness", "#0f3d5c"),
        ("Body battery", "body_battery", "#d97a06"),
        ("HRV (ms)", "hrv_valor_ms", "#8a2a5e"),
        ("ACWR", "acwr", "#c62839"),
    ]
    graficas = {}
    for etiqueta, campo, color in metricas:
        fechas, valores = _serie_numerica(filas, campo)
        graficas[etiqueta] = generar_svg_linea(fechas, valores, color=color)
    return graficas
