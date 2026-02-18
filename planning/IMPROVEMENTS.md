# Hoja de Ruta: Reestructuración Industrial

Este documento centraliza las mejoras pendientes para profesionalizar la integración y adaptarla a un uso industrial/SCADA.

## ✅ Tareas de Limpieza (Completadas)

Eliminación de código huérfano y optimización del flujo.

* **Limpieza de `config_flow.py`**:
  * Eliminado `async_step_pv_model_delete_select`.
  * Eliminadas constantes obsoletas y variables de estado sin uso.
  * Garantizado el reset de `self.temp_data` en cada rama del menú.
* **Traducciones**: Claves de borrado eliminadas en `es.json` y `en.json`.

---

## 🏗️ Fase Actual: Agrupación Lógica y Escalabilidad

El objetivo es pasar de un modelo de "entidades sueltas" a "Dispositivos Lógicos" que agrupen la información de forma coherente.

### 1. Gestión de Orientaciones

* **Base de Datos**: Crear un catálogo de "Orientaciones" (ej: "Tejado Principal", "Shed Este").
* **Atributos**: Cada orientación define un par único de (Inclinación, Azimut).
* **Configuración**: Al crear un String, se seleccionará una orientación del catálogo en lugar de introducir grados manualmente.

### 2. Rediseño de Dispositivos (Servicios)

Refactorizar `DeviceInfo` en `sensor.py` para agrupar entidades en 3 dispositivos maestros:

1. **"Grupos de Sensores"**: Centraliza los estados de salud y diagnósticos de todos los sensores físicos.
2. **"Hub de Orientación: [Nombre]"**: Se creará un dispositivo por cada orientación configurada (ej: "Orientación: Sur"). Todos los Strings asociados a esa orientación aparecerán como entidades dentro de este dispositivo.
3. **"Catálogo de Módulos"**: Dispositivo informativo con los modelos de paneles registrados.

---

## ✅ Logros Recientes

* Implementación de **Modelo Híbrido (Directa + Difusa)** usando `cloud_coverage`.
* Creación de **Entidad Virtual de Estado** para Grupos de Sensores.
* Vinculación dinámica de dispositivos basada en el sensor de irradiancia.
* Reordenación de interfaz para mejor UX.
