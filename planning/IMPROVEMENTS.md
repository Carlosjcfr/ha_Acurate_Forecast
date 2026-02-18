# 📄 Plan de Optimización y Limpieza: `config_flow.py`

Basado en el análisis de tu código actual frente al último diagrama de flujo adjunto y tus solicitudes recientes (eliminar borrados nativos, reestructurar menús), he detectado los siguientes puntos a intervenir.

### 1. 🗑️ Código Muerto (A Eliminar)

Funciones que existen en el archivo pero ya no son accesibles desde ningún menú o no son necesarias delegando en Home Assistant.

* **`async_step_pv_model_delete_select`**:
  * *Motivo:* En el paso anterior solicitaste retirar la opción de borrar modelos del menú "Acciones". Al no haber botón, esta función es inalcanzable.
* **Constantes `ACTION_DELETE` / `ACTION_EDIT` / `ACTION_CREATE`**:
  * *Motivo:* Se definieron al principio de la clase pero no se están utilizando en la lógica de flujo actual, que es explícita por pasos (`step_id`).
* **`self.selected_action`**:
  * *Motivo:* Variable de estado no utilizada en el nuevo esquema modular.

### 2. ⚡ Optimizaciones y Refactorización

Mejoras para reducir duplicidad y asegurar robustez.

* **Consolidación de Helpers de Formularios (`_show_...`)**:
  * *Estado Actual:* Las funciones `_show_pv_model_form` y `_show_sensor_group_form` están bien planteadas, pero haremos una revisión para asegurar que manejan `vol.UNDEFINED` de forma limpia en lugar de valores hardcoded vacíos donde no aplica.
* **Limpieza de `temp_data`**:
  * *Acción:* Asegurar que `self.temp_data` se limpie correctamente al iniciar un nuevo flujo para evitar "contaminación" cruzada si el usuario cancela y vuelve a entrar sin cerrar el diálogo.
* **Validación de Ramas**:
  * **Rama Strings:** El diagrama muestra `Seleccionar Fabricante` -> `Formulario String`. El código lo implementa dividido en dos pasos (`select_brand` y `details`) por limitaciones técnicas de HA (no se pueden filtrar modelos dinámicamente sin recargar el paso). *Se mantiene así por necesidad técnica, pero se limpia el código.*

### 3. 🔍 Cambios en Traducciones (Limpieza)

* Eliminar las claves huérfanas en `es.json` y `en.json` referencias a `pv_model_delete_select` para mantener los archivos de idioma limpios.

---

### 🛠️ Hoja de Ruta de la Ejecución
