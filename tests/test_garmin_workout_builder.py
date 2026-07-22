from fuentes.garmin_workout_builder import construir_workout_natacion
from fuentes.swimmingdsl_cliente import BloqueNado, parsear_codigo_dsl

CODIGO_CON_SECCIONES = """session generated_speed {
  warmup {
    swim 500 m easy pace 120
  }
  main {
    30 x swim 50 m butterfly hard pace 60 rest 45 s
  }
  cooldown {
    swim 500 m easy pace 130
  }
}"""

CODIGO_SIN_REPETICION = """session generated_recovery {
  swim 3000 m easy pace 140
}"""


def test_construir_workout_natacion_tiene_el_nombre_y_deporte_correctos():
    bloques = parsear_codigo_dsl(CODIGO_CON_SECCIONES)
    workout = construir_workout_natacion("Entreno de velocidad", bloques)

    datos = workout.to_dict()
    assert datos["workoutName"] == "Entreno de velocidad"
    assert datos["sportType"]["sportTypeKey"] == "swimming"


def test_construir_workout_natacion_genera_un_paso_por_bloque_sin_repeticion():
    bloques = parsear_codigo_dsl(CODIGO_SIN_REPETICION)
    workout = construir_workout_natacion("Recuperacion", bloques)

    pasos = workout.to_dict()["workoutSegments"][0]["workoutSteps"]
    assert len(pasos) == 1
    assert pasos[0]["type"] == "ExecutableStepDTO"
    assert pasos[0]["endConditionValue"] == 3000.0
    assert pasos[0]["endCondition"]["conditionTypeKey"] == "distance"


def test_construir_workout_natacion_envuelve_las_repeticiones_en_repeat_group():
    bloques = parsear_codigo_dsl(CODIGO_CON_SECCIONES)
    workout = construir_workout_natacion("Velocidad", bloques)

    pasos = workout.to_dict()["workoutSegments"][0]["workoutSteps"]
    assert len(pasos) == 3
    grupo_repeticion = pasos[1]
    assert grupo_repeticion["type"] == "RepeatGroupDTO"
    assert grupo_repeticion["numberOfIterations"] == 30
    assert len(grupo_repeticion["workoutSteps"]) == 2
    assert grupo_repeticion["workoutSteps"][0]["endConditionValue"] == 50.0
    assert grupo_repeticion["workoutSteps"][1]["endCondition"]["conditionTypeKey"] == "time"
    assert grupo_repeticion["workoutSteps"][1]["endConditionValue"] == 45.0


def test_construir_workout_natacion_omite_paso_de_descanso_si_no_hay():
    bloques = [
        BloqueNado(
            seccion="main",
            repeticiones=10,
            distancia_m=25,
            estilo="freestyle",
            intensidad="hard",
            pace_segundos=20,
            descanso_segundos=None,
        )
    ]
    workout = construir_workout_natacion("Sin descanso", bloques)

    grupo_repeticion = workout.to_dict()["workoutSegments"][0]["workoutSteps"][0]
    assert len(grupo_repeticion["workoutSteps"]) == 1


def test_construir_workout_natacion_calcula_duracion_estimada():
    bloques = parsear_codigo_dsl(CODIGO_CON_SECCIONES)
    workout = construir_workout_natacion("Velocidad", bloques)

    assert workout.to_dict()["estimatedDurationInSecs"] == 3500


def test_construir_workout_natacion_incluye_descripcion_legible():
    bloques = parsear_codigo_dsl(CODIGO_CON_SECCIONES)
    workout = construir_workout_natacion("Velocidad", bloques)

    descripcion = workout.to_dict()["description"]
    assert "500m easy" in descripcion
    assert "30x" in descripcion
    assert "butterfly" in descripcion
    assert "descanso 45s" in descripcion


def test_construir_workout_natacion_tipos_de_paso_por_seccion():
    bloques = parsear_codigo_dsl(CODIGO_CON_SECCIONES)
    workout = construir_workout_natacion("Velocidad", bloques)

    pasos = workout.to_dict()["workoutSegments"][0]["workoutSteps"]
    assert pasos[0]["stepType"]["stepTypeKey"] == "warmup"
    assert pasos[2]["stepType"]["stepTypeKey"] == "cooldown"
