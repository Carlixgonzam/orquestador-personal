import os

from fuentes.notas_cliente import escanear_repo_notas, escanear_todos_los_repos_notas

RUTA_NOTAS_MOCK = os.path.join(os.path.dirname(__file__), "fixtures", "notas_mock")
RUTA_REPO_ALGORITMOS = os.path.join(RUTA_NOTAS_MOCK, "notas-algoritmos")
RUTA_REPO_INEXISTENTE = os.path.join(RUTA_NOTAS_MOCK, "notas-que-no-existe")


def test_escanear_repo_notas_encuentra_las_dos_macros_del_fixture():
    hallazgos = escanear_repo_notas("notas-algoritmos", RUTA_REPO_ALGORITMOS)

    assert len(hallazgos) == 2
    macros_encontradas = {hallazgo.macro for hallazgo in hallazgos}
    assert macros_encontradas == {"important", "examen"}


def test_escanear_repo_notas_extrae_el_contenido_de_la_macro():
    hallazgos = escanear_repo_notas("notas-algoritmos", RUTA_REPO_ALGORITMOS)
    hallazgo_important = next(hallazgo for hallazgo in hallazgos if hallazgo.macro == "important")

    assert hallazgo_important.contenido == "Dijkstra no funciona con pesos negativos"
    assert hallazgo_important.repo == "notas-algoritmos"


def test_escanear_repo_notas_no_falla_si_el_repo_no_existe_localmente():
    hallazgos = escanear_repo_notas("notas-que-no-existe", RUTA_REPO_INEXISTENTE)
    assert hallazgos == []


def test_escanear_todos_los_repos_notas_combina_existentes_e_inexistentes():
    repos_notas = [
        {"nombre": "notas-algoritmos", "ruta_local": RUTA_REPO_ALGORITMOS},
        {"nombre": "notas-que-no-existe", "ruta_local": RUTA_REPO_INEXISTENTE},
    ]

    hallazgos = escanear_todos_los_repos_notas(repos_notas)

    assert len(hallazgos) == 2
    assert all(hallazgo.repo == "notas-algoritmos" for hallazgo in hallazgos)
