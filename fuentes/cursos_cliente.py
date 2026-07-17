import yaml


def cargar_nombres_cursos(ruta_config: str) -> dict[str, str]:
    with open(ruta_config, encoding="utf-8") as archivo_config:
        contenido = yaml.safe_load(archivo_config)
    return contenido.get("nombres_cursos", {})
