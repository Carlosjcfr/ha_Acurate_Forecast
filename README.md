# ☀️ Accurate Solar Forecast for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Maintainer](https://img.shields.io/badge/maintainer-%40tu_usuario-blue)](https://github.com/tu_usuario)
[![version](https://img.shields.io/badge/version-1.0.0-green)]()

**Accurate Forecast** es una integración personalizada para Home Assistant diseñada para estimar la producción fotovoltaica con alta precisión física y geométrica.

A diferencia de las estimaciones simples, este componente utiliza **motores de transposición de irradiancia**, permitiendo simular múltiples strings con diferentes orientaciones utilizando **un único sensor de referencia** (piranómetro o sensor solar).

## ✨ Características Principales

### 📐 Motor de Transposición Geométrica

Olvídate de comprar múltiples sensores de irradiancia.

* Calcula la radiación incidente en cualquier superficie (orientación/inclinación).
* Utiliza la posición solar en tiempo real (Azimut y Elevación) para calcular el **Ángulo de Incidencia (AOI)**.
* Transpone matemáticamente la lectura de un sensor origen a ilimitados strings virtuales.

### 💾 Base de Datos de Paneles (PV Database)

Sistema de gestión de inventario integrado.

* **Define una vez, usa siempre:** Crea modelos de tus placas solares (Potencia, Coeficientes, NOCT) y guárdalos en la base de datos interna.
* **Reutilizable:** Asigna el mismo modelo de panel a diferentes strings sin volver a introducir fichas técnicas.

### 🌡️ Física Térmica Avanzada

El calor reduce el rendimiento solar. Esta integración calcula las pérdidas (*derating*) seleccionando automáticamente la mejor lógica disponible según tus sensores:

| Prioridad | Método | Sensores Necesarios | Precisión |
| :--- | :--- | :--- | :--- |
| 1️⃣ | **Medición Directa** | Temp. Panel | ⭐⭐⭐ (Máxima) |
| 2️⃣ | **Modelo Faiman** | Ambiente + Viento | ⭐⭐ (Alta) |
| 3️⃣ | **Modelo NOCT** | Ambiente | ⭐ (Estándar) |

### ⚡ Gestión Multi-String

* Soporte para ilimitados strings.
* Configuración independiente de Azimut, Inclinación (Tilt) y número de paneles por string.

### ⚙️ Configuración 100% UI

* Olvídate de editar YAML.
* **Config Flow Nativo:** Asistente paso a paso para añadir modelos a la base de datos o configurar nuevos strings.
* Menús dinámicos con selectores.

---

## 🚀 Instalación

### Opción 1: HACS (Recomendado)

1. Añade este repositorio como **Custom Repository** en HACS.
2. Busca "Accurate Forecast" e instala.
3. Reinicia Home Assistant.

### Opción 2: Manual

1. Descarga la carpeta `accurate_forecast`.
2. Cópiala dentro de `config/custom_components/`.
3. Reinicia Home Assistant.

---

## 📖 Uso y Configuración

Ve a **Ajustes** > **Dispositivos y Servicios** > **Añadir Integración** > **Accurate Forecast**.

### Paso 1: Crear un Modelo de Panel

Selecciona la opción **"Añadir Nuevo Modelo de Panel"**. Necesitarás la ficha técnica de tu placa:

* **Nombre:** (Ej: `Longi 450W Hi-MO`)
* **P_stc:** Potencia Pico (W)
* **Gamma:** Coeficiente de Temperatura (%/°C)
* **NOCT:** Temperatura de operación nominal.

### Paso 2: Crear un String

Selecciona **"Configurar Nuevo String"**:

1. Elige el modelo de panel (desde tu base de datos).
2. Introduce el número de paneles.
3. Define la orientación (Azimut) e inclinación del string.
4. Selecciona tu **sensor de irradiancia de referencia** y define cómo está instalado (plano, inclinado, etc.).

---

## 🧠 Cómo funciona (La Ciencia)

El componente realiza los siguientes cálculos en cada actualización:

1. **Geometría Solar:** Obtiene la posición del sol (`sun.sun`).
2. **Cálculo AOI:** Determina el ángulo de incidencia tanto para el sensor de referencia como para el panel objetivo.
3. **Factor Geométrico:** `Irradiancia_Target = Irradiancia_Ref * (cos(θ_target) / cos(θ_ref))`
4. **Modelo Térmico:** Calcula la temperatura de la célula ($T_{cell}$) basándose en la disipación de calor (viento) o calentamiento pasivo.
5. **Potencia Final:** Aplica el coeficiente de pérdidas por temperatura a la irradiancia transpuesta.

---

## 📄 Licencia

PolyForm Strict License 1.0.0 ->
<https://polyformproject.org/licenses/strict/1.0.0>
