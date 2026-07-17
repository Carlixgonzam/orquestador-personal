# orquestador-personal

Sistema de orquestación personal que decide, cada día, qué tareas académicas hacer según mi estado fisiológico (medido con Garmin), respetando mi horario fijo de clases y entrenamiento de natación.

El sistema lee mi disposición para entrenar, HRV, estado de entrenamiento, ACWR, body battery y otras métricas de Garmin Connect, las cruza con mis tareas académicas pendientes y mi plan de entrenamiento de la semana, y genera un archivo `hoy.md` con las tareas recomendadas por cada hueco libre del día y una recomendación de entrenamiento.

## Arquitectura de repos

El sistema completo vive en cuatro tipos de repos separados. Este repo (`orquestador-personal`) solo contiene código: no tiene datos propios.

- **orquestador-personal** (este repo): modelos, clientes de datos, motor de reglas y generador de reporte.
- **pendientes**: repo separado con un archivo `tareas.yaml` con las tareas académicas pendientes (curso, título, deadline, energía requerida, peso académico, estado).
- **entrenamiento**: repo separado con archivos `plan-semana-XX.yaml` (uno por semana ISO) con las sesiones de entrenamiento planeadas.
- **notas-*** (seis repos, uno por curso: dalgo, moviles, web, fisica2, matematica, gobierno-procesos): repos de notas independientes, referenciados solo por ruta local en `config/config.yaml`. Nunca se clonan como submódulo ni se copian dentro de este repo.

`orquestador-personal` solo lee de los repos de entrenamiento y notas. Sí escribe en `pendientes/tareas.yaml`, pero únicamente a través de la interfaz web (agregar, completar o eliminar tareas) — nunca automáticamente durante `ejecutar_diario.py`.

## Estructura del código

```
config/config.yaml           horario fijo, umbrales y rutas a los demás repos
modelo/                       dataclasses del dominio (tarea, sesion_entrenamiento, estado_fisiologico, bloque_fijo, hueco_libre)
fuentes/                      clientes que leen (y en el caso de pendientes, tambien escriben) Garmin, pendientes, entrenamiento, notas y el horario fijo
motor/                        jerarquia de reglas de decision y recomendador de entrenamiento
salida/                       generador del reporte hoy.md a partir de una plantilla Jinja
scripts/ejecutar_diario.py    entry point que orquesta todo el flujo
interfaz/app.py               interfaz web local (Flask) para ver hoy.md y gestionar tareas sin editar YAML a mano
tests/                        tests con pytest y fixtures mock (sin tocar Garmin ni los repos reales)
```

## La jerarquía de decisión

`motor/priorizador.py` implementa cinco reglas, evaluadas en este orden:

1. **Bloque fijo activo**: si el momento actual cae dentro de una clase o entrenamiento de `bloques_fijos`, no se genera ninguna recomendación, se devuelve directamente ese bloque.
2. **Sobreentrenamiento**: si `training_status` es `Overreaching` o `Detraining`, solo se recomiendan tareas de energía baja, sin entrenamiento adicional fuera del plan fijo.
3. **ACWR alto**: si el ratio de carga aguda/crónica supera `acwr_limite` (default 1.5), se recomienda reducir la intensidad de la próxima sesión planeada y se prioriza lo académico.
4. **HRV desbalanceado + body battery bajo**: si `hrv_status` es `unbalanced` y el body battery está por debajo de `body_battery_bajo` (default 40), y no es lunes/martes/jueves antes de las 9am (por el entrenamiento matutino ya contemplado), es un día de carga baja: solo tareas administrativas.
5. **Matching fino**: si ninguna regla anterior aplica, el body battery se empareja con la energía requerida de cada tarea usando los umbrales de `config.yaml`.

Dentro de cada nivel de energía, las tareas se ordenan por cercanía del deadline y luego por peso académico descendente. Nunca se toca un bloque fijo de entrenamiento ya confirmado: `motor/recomendador_entrenamiento.py` solo decide si la sesión planeada se mantiene, se reduce en intensidad o se reemplaza por recuperación activa dentro del mismo horario.

## Configuración

### Variables de entorno

- `GARMIN_EMAIL`: correo de la cuenta de Garmin Connect.
- `GARMIN_PASSWORD`: contraseña de la cuenta de Garmin Connect.

El token de sesión se guarda localmente en `~/.orquestador_personal/token_garmin` después del primer login, para no reautenticar en cada corrida.

### config/config.yaml

Contiene:

- `bloques_fijos`: el horario fijo del semestre (clases y entrenamiento de natación). Nunca se recomienda nada dentro de estos bloques.
- `umbrales`: `acwr_limite`, `body_battery_bajo`, `body_battery_medio`.
- `rutas_repos`: rutas locales a los repos `pendientes` y `entrenamiento`.
- `repos_notas`: nombre y ruta local de cada uno de los seis repos de notas.

Por defecto, `rutas_repos` y `repos_notas` asumen que todos los repos están clonados como hermanos de `orquestador-personal` (`../pendientes`, `../entrenamiento`, `../notas-algoritmos`, etc.). Ajusta esas rutas a donde tengas cada repo clonado localmente.

## Cómo correr localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install .

export GARMIN_EMAIL="tu-correo@ejemplo.com"
export GARMIN_PASSWORD="tu-contrasena"

python scripts/ejecutar_diario.py
```

Esto genera `hoy.md` en la raíz del repo con el horario fijo del día, el resumen del estado fisiológico, las tareas recomendadas por hueco libre, la recomendación de entrenamiento y las alertas si aplica alguna regla de bloqueo.

## Interfaz web

Para no tener que editar `tareas.yaml` a mano, hay una interfaz web local minimalista:

```bash
python interfaz/app.py
```

Esto levanta un servidor en `http://127.0.0.1:5050` (correrlo desde la raíz del repo, con el entorno virtual activado). Desde ahí puedes:

- Ver el último `hoy.md` generado.
- Regenerar el reporte con un botón (vuelve a llamar a Garmin y a las reglas de decisión).
- Agregar una tarea nueva con un formulario (curso, título, deadline, energía requerida, créditos).
- Marcar una tarea como completada o eliminarla.
- Ver, debajo de cada tarea, los hallazgos marcados con `\begin{alertbox}...\end{alertbox}` o `\begin{examenbox}...\end{examenbox}` en el repo de notas del curso correspondiente (si ese repo existe localmente). Estos son entornos de `preamble.sty`, la plantilla LaTeX real de las notas.

Es un servidor de desarrollo Flask pensado para uso local y personal, no para exponerlo a internet.

## Cómo correr los tests

```bash
pip install ".[dev]"
pytest
```

Los tests usan fixtures mock en `tests/fixtures/` (incluyendo `garmin_mock.json`) y nunca hacen llamadas reales a Garmin ni a los repos de pendientes/entrenamiento/notas.

## GitHub Action

`.github/workflows/reporte_diario.yml` corre `scripts/ejecutar_diario.py` todas las mañanas (10:30 UTC), clonando también los repos `pendientes` y `entrenamiento` como directorios hermanos dentro del runner. Sube `hoy.md` como artifact y lo commitea de vuelta al repo.

Secrets necesarios en el repo de GitHub:

- `GARMIN_EMAIL`, `GARMIN_PASSWORD`: credenciales de Garmin Connect.
- `TOKEN_REPOS_PRIVADOS`: token de acceso personal con permiso de lectura sobre los repos `pendientes` y `entrenamiento`, si son privados.

## Cómo actualizar el horario fijo cada semestre

El horario fijo vive completo en `bloques_fijos` dentro de `config/config.yaml`. Al empezar un semestre nuevo:

1. Reemplaza la lista `bloques_fijos` con las clases y entrenamientos del nuevo semestre (día de la semana, hora de inicio, hora de fin, tipo, nombre y código si aplica).
2. Revisa `tests/fixtures/config_mock.yaml`: es un horario de prueba reducido, independiente del real, y no necesita cambiar salvo que quieras probar otros casos.
3. Corre `pytest` para confirmar que el cálculo de huecos libres sigue funcionando con el horario nuevo.

No hace falta tocar ningún otro archivo: `fuentes/horario_cliente.py` y el resto del motor leen `bloques_fijos` dinámicamente desde `config.yaml`.
