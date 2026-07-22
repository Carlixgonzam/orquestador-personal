from garminconnect.workout import (
    ConditionType,
    ExecutableStep,
    StepType,
    SwimmingWorkout,
    TargetType,
    WorkoutSegment,
    create_repeat_group,
)

from fuentes.swimmingdsl_cliente import BloqueNado

OBJETIVO_SIN_META = {
    "workoutTargetTypeId": TargetType.NO_TARGET,
    "workoutTargetTypeKey": "no.target",
    "displayOrder": 1,
}

TIPO_DE_PASO_POR_SECCION = {
    "warmup": (StepType.WARMUP, "warmup"),
    "main": (StepType.INTERVAL, "interval"),
    "cooldown": (StepType.COOLDOWN, "cooldown"),
}


def _paso_de_distancia(bloque: BloqueNado, orden: int) -> ExecutableStep:
    id_tipo_paso, clave_tipo_paso = TIPO_DE_PASO_POR_SECCION.get(bloque.seccion, (StepType.INTERVAL, "interval"))
    return ExecutableStep(
        stepOrder=orden,
        stepType={"stepTypeId": id_tipo_paso, "stepTypeKey": clave_tipo_paso, "displayOrder": id_tipo_paso},
        endCondition={
            "conditionTypeId": ConditionType.DISTANCE,
            "conditionTypeKey": "distance",
            "displayOrder": 3,
            "displayable": True,
        },
        endConditionValue=float(bloque.distancia_m),
        targetType=OBJETIVO_SIN_META,
    )


def _paso_de_descanso(segundos: int, orden: int) -> ExecutableStep:
    return ExecutableStep(
        stepOrder=orden,
        stepType={"stepTypeId": StepType.REST, "stepTypeKey": "rest", "displayOrder": StepType.REST},
        endCondition={
            "conditionTypeId": ConditionType.TIME,
            "conditionTypeKey": "time",
            "displayOrder": 2,
            "displayable": True,
        },
        endConditionValue=float(segundos),
        targetType=OBJETIVO_SIN_META,
    )


def _describir_bloque(bloque: BloqueNado) -> str:
    partes = []
    if bloque.repeticiones > 1:
        partes.append(f"{bloque.repeticiones}x")
    partes.append(f"{bloque.distancia_m}m")
    if bloque.estilo:
        partes.append(bloque.estilo)
    if bloque.intensidad:
        partes.append(bloque.intensidad)
    if bloque.descanso_segundos:
        partes.append(f"descanso {bloque.descanso_segundos}s")
    return " ".join(partes)


def _duracion_estimada_segundos(bloques: list[BloqueNado]) -> int:
    total = 0.0
    for bloque in bloques:
        tiempo_nado = (bloque.distancia_m / 100.0) * bloque.pace_segundos
        tiempo_descanso = bloque.descanso_segundos or 0
        total += bloque.repeticiones * (tiempo_nado + tiempo_descanso)
    return round(total)


def construir_workout_natacion(nombre: str, bloques: list[BloqueNado]) -> SwimmingWorkout:
    pasos = []
    orden = 1
    for bloque in bloques:
        paso_nado = _paso_de_distancia(bloque, orden)
        orden += 1
        if bloque.repeticiones > 1:
            pasos_internos = [paso_nado]
            if bloque.descanso_segundos:
                pasos_internos.append(_paso_de_descanso(bloque.descanso_segundos, orden))
                orden += 1
            pasos.append(create_repeat_group(bloque.repeticiones, pasos_internos, orden))
            orden += 1
        else:
            pasos.append(paso_nado)

    segmento = WorkoutSegment(
        segmentOrder=1,
        sportType={"sportTypeId": 4, "sportTypeKey": "swimming", "displayOrder": 3},
        workoutSteps=pasos,
    )

    return SwimmingWorkout(
        workoutName=nombre,
        estimatedDurationInSecs=_duracion_estimada_segundos(bloques),
        workoutSegments=[segmento],
        description="; ".join(_describir_bloque(bloque) for bloque in bloques),
    )
