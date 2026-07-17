import glob
import os
import re
from dataclasses import dataclass

PATRON_MACROS_DE_INTERES = re.compile(r"\\(important|examen)\{([^}]*)\}")


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
        for coincidencia in PATRON_MACROS_DE_INTERES.finditer(contenido_archivo):
            hallazgos.append(
                HallazgoNota(
                    repo=nombre_repo,
                    archivo=ruta_archivo,
                    macro=coincidencia.group(1),
                    contenido=coincidencia.group(2),
                )
            )
    return hallazgos


def escanear_todos_los_repos_notas(repos_notas: list[dict]) -> list[HallazgoNota]:
    hallazgos_totales = []
    for repo in repos_notas:
        hallazgos_totales.extend(escanear_repo_notas(repo["nombre"], repo["ruta_local"]))
    return hallazgos_totales
