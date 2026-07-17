import glob
import os
import re
from dataclasses import dataclass

NOMBRES_DE_MACRO_POR_ENTORNO = {
    "alertbox": "important",
    "examenbox": "examen",
}

PATRON_ENTORNOS_DE_INTERES = re.compile(
    r"\\begin\{(" + "|".join(NOMBRES_DE_MACRO_POR_ENTORNO) + r")\}(?:\[[^\]]*\])?\s*(.*?)\\end\{\1\}",
    re.DOTALL,
)


@dataclass
class HallazgoNota:
    repo: str
    archivo: str
    macro: str
    contenido: str


def escanear_repo_notas(nombre_repo: str, ruta_local: str) -> list[HallazgoNota]:
    ruta_absoluta = os.path.expanduser(ruta_local)
    if not os.path.isdir(ruta_absoluta):
        return []

    hallazgos = []
    patron_busqueda = os.path.join(ruta_absoluta, "**", "*.tex")
    for ruta_archivo in glob.glob(patron_busqueda, recursive=True):
        with open(ruta_archivo, encoding="utf-8") as archivo_notas:
            contenido_archivo = archivo_notas.read()
        for coincidencia in PATRON_ENTORNOS_DE_INTERES.finditer(contenido_archivo):
            nombre_entorno = coincidencia.group(1)
            hallazgos.append(
                HallazgoNota(
                    repo=nombre_repo,
                    archivo=ruta_archivo,
                    macro=NOMBRES_DE_MACRO_POR_ENTORNO[nombre_entorno],
                    contenido=coincidencia.group(2).strip(),
                )
            )
    return hallazgos


def escanear_todos_los_repos_notas(repos_notas: list[dict]) -> list[HallazgoNota]:
    hallazgos_totales = []
    for repo in repos_notas:
        hallazgos_totales.extend(escanear_repo_notas(repo["nombre"], repo["ruta_local"]))
    return hallazgos_totales


def curso_desde_nombre_repo_notas(nombre_repo: str) -> str:
    return nombre_repo.removeprefix("notas-").replace("-", "_")


def hallazgos_por_curso(repos_notas: list[dict]) -> dict[str, list[HallazgoNota]]:
    resultado = {}
    for repo in repos_notas:
        curso = curso_desde_nombre_repo_notas(repo["nombre"])
        resultado[curso] = escanear_repo_notas(repo["nombre"], repo["ruta_local"])
    return resultado
