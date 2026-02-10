# Flujo de Trabajo Recomendado

Este documento describe cómo usar la carpeta `planning` para gestionar el proyecto.

## Estructura de Archivos

- **TASKS.md**: Tablero de gestión diaria. Úsalo para saber qué hacer "ahora".
- **ROADMAP.md**: Visión general. Úsalo para no perder el norte del proyecto.
- **DECISIONS.md** (Opcional): Para registrar decisiones técnicas complejas (ADRs).

## Ciclo de Trabajo (Workflow)

1. **Captura (Inbox)**:
    - Cuando tengas una nueva idea o encuentres un bug, añádelo inmediatamente a la sección `Backlog` en `TASKS.md`. No lo pienses mucho, solo captúralo.

2. **Planificación (Sprint Planning)**:
    - Antes de empezar a programar, mueve las tareas que quieres abordar de `Backlog` a `To Do`.
    - Verifica si alguna tarea se alinea con el `ROADMAP.md`.

3. **Ejecución**:
    - Mueve una tarea de `To Do` a `In Progress`.
    - Trabaja en el código.
    - Mantén el foco en esa única tarea.

4. **Finalización**:
    - Mueve la tarea a `Done` en `TASKS.md`.
    - Si la tarea implica un cambio visible para el usuario, actualiza el `CHANGELOG.md` en la raíz del proyecto.
    - Haz commit y push de tus cambios.

## Consejos

- Mantén `TASKS.md` limpio. Si la lista de `Done` crece mucho, bórrala o archívala.
- Revisa `ROADMAP.md` una vez al mes para ajustar objetivos.
