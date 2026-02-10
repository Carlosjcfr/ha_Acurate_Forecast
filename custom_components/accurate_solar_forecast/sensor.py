import math
import logging
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfPower, UnitOfTemperature, UnitOfSpeed
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from .const import *

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    # Solo creamos sensor si es un String (no si solo añadimos un modelo)
    if CONF_STRING_NAME in config_entry.data:
        db = hass.data[DOMAIN]["db"]
        async_add_entities([SolarStringSensor(hass, config_entry.data, db)], update_before_add=True)

class SolarStringSensor(SensorEntity):
    def __init__(self, hass, config_entry, db):
        self.hass = hass
        self._config = config_entry # config_entry.data really
        self._db = db
        
        # Recuperar datos del modelo desde la DB usando el nombre
        model_name = self._config.get(CONF_PANEL_MODEL)
        # Búsqueda inversa simple (nombre -> datos)
        self._panel_data = None
        if db and db.data:
            # Buscar por nombre en los valores del dict
            for v in db.data.values():
                if v.get("name") == model_name:
                    self._panel_data = v
                    break
        
        self._attr_name = self._config.get(CONF_STRING_NAME)
        self._attr_unique_id = f"str_{self._config.get(CONF_STRING_NAME).lower().replace(' ', '_')}"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_value = 0
        self._attr_extra_state_attributes = {}

    @property
    def check_config(self):
        return self._panel_data is not None

    def get_float_state(self, entity_id, default=0.0):
        state = self.hass.states.get(entity_id)
        if state and state.state not in ["unavailable", "unknown"]:
            try:
                return float(state.state)
            except ValueError:
                pass
        return default

    def calculate_cos_incidence(self, sun_az, sun_el, panel_az, panel_tilt):
        """Calcula el coseno del ángulo de incidencia."""
        # Convertir todo a radianes
        # Azimuth en HA: 0=Norte, 90=Este, 180=Sur, 270=Oeste
        # Tilt: 0=Horizontal, 90=Vertical
        
        # Zenit Solar = 90 - Elevación
        sol_zenith_rad = math.radians(90 - sun_el)
        sol_az_rad = math.radians(sun_az)
        
        panel_tilt_rad = math.radians(panel_tilt)
        panel_az_rad = math.radians(panel_az)

        # Fórmula general del ángulo de incidencia
        # cos(AOI) = cos(ZenitSol)*cos(TiltPanel) + sin(ZenitSol)*sin(TiltPanel)*cos(AzSol - AzPanel)
        cos_theta = (math.cos(sol_zenith_rad) * math.cos(panel_tilt_rad)) + \
                    (math.sin(sol_zenith_rad) * math.sin(panel_tilt_rad) * math.cos(sol_az_rad - panel_az_rad))
        
        return max(0, cos_theta)

    @callback
    def _update_logic(self, event=None):
        if not self.check_config:
            _LOGGER.warning("Datos del panel no encontrados para el cálculo.")
            return

        # 1. Datos Solares
        sun_state = self.hass.states.get("sun.sun")
        if not sun_state:
            return
        
        sun_az = float(sun_state.attributes.get("azimuth", 180))
        sun_el = float(sun_state.attributes.get("elevation", 0))

        if sun_el <= 0:
            self._attr_native_value = 0
            self._attr_extra_state_attributes = {
                "estado_solar": "Noche",
                "sun_elevation": sun_el
            }
            self.async_write_ha_state()
            return

        # 2. Datos del Sensor de Referencia (Irradiancia)
        ref_sensor = self._config.get(CONF_REF_SENSOR)
        irr_ref = self.get_float_state(ref_sensor, 0.0)
        
        # 3. Datos Ambientales
        temp_sensor = self._config.get(CONF_TEMP_SENSOR)
        t_amb = self.get_float_state(temp_sensor, 25.0)
        
        wind_sensor = self._config.get(CONF_WIND_SENSOR)
        wind_speed = 1.0 # Default suave si no hay sensor
        if wind_sensor:
            wind_speed = self.get_float_state(wind_sensor, 1.0)

        # 4. Cálculos Geométricos para Transposición
        # Panel Destino
        target_az = self._config.get(CONF_AZIMUTH)
        target_tilt = self._config.get(CONF_TILT)
        cos_theta_target = self.calculate_cos_incidence(sun_az, sun_el, target_az, target_tilt)

        # Sensor Referencia
        ref_az = self._config.get(CONF_REF_ORIENTATION)
        ref_tilt = self._config.get(CONF_REF_TILT)
        cos_theta_ref = self.calculate_cos_incidence(sun_az, sun_el, ref_az, ref_tilt)

        # Transposición de Irradiancia
        # Evitamos división por cero o valores absurdos si el sensor de ref está muy oblicuo
        if cos_theta_ref < 0.05:
            # Fallback: Si el sensor ref no "ve" bien el sol, asumimos que irr_ref es difusa/global
            # y no aplicamos factor geométrico agresivo, o lo limitamos.
            # Para simplificar: si el ref no ve el sol, la estimación es poco fiable.
            geometric_factor = 0 if irr_ref > 10 else 1 
        else:
            geometric_factor = cos_theta_target / cos_theta_ref
        
        irr_target = irr_ref * geometric_factor

        # 5. Modelo Térmico (Temperatura de Célula)
        # Usamos fórmula NOCT estándar ajustada: Tcell = Tamb + (NOCT - 20) * (Irr / 800)
        # Si quisiéramos usar viento (modelo Faiman), sería más complejo.
        # Por robustez inicial, usamos NOCT que viene en la DB.
        noct = self._panel_data.get("noct", 45)
        t_cell = t_amb + (irr_target / 800) * (noct - 20)

        # 6. Cálculo de Potencia DC
        # P = P_stc * (Irr / 1000) * [1 + gamma * (Tcell - 25)]
        p_stc = self._panel_data.get("p_stc", 400)
        gamma = self._panel_data.get("gamma", -0.4) / 100.0 # Convertir % a decimal
        num_panels_series = self._config.get(CONF_NUM_PANELS, 1)
        num_strings_parallel = self._config.get(CONF_NUM_STRINGS, 1)

        # Factor térmico
        # Asumimos que Gamma aplica principalmente a Potencia y Voltaje.
        # Coeficiente de voltaje suele ser similar a gamma de potencia (negativo).
        temp_diff = t_cell - 25
        temp_factor_power = 1 + (gamma * temp_diff)
        
        # Potencia unitaria STC * IrrRatio * TempFactor
        power_unit = p_stc * (irr_target / 1000.0) * temp_factor_power
        
        # Potencia total = Potencia Unitaria * Total Paneles
        total_panels = num_panels_series * num_strings_parallel
        total_power = max(0, power_unit * total_panels)

        # --- CÁLCULO DE TENSIÓN E INTENSIDAD (ESTIMACIÓN) ---
        vmp = self._panel_data.get("vmp", 30.0)
        imp = self._panel_data.get("imp", 10.0)
        
        # Voltaje: Depende temperatura (Gamma) y NO de irradiancia (idealmente, aunque baja un poco con poca luz)
        # V_string = Vmp * N_series * [1 + Gamma_V * (Tcell - 25)]
        # Usamos Gamma de Potencia como aproximación para Voltaje si no tenemos Beta_Voc
        # (El voltaje cae con el calor, igual que la potencia)
        v_string = vmp * num_panels_series * temp_factor_power
        
        # Corriente: Depende linealmente de irradiancia y poco de temperatura
        # I_string = Imp * (Irr / 1000) * N_parallel
        # (Ignoramos pequeño coeficiente positivo de temperatura para corriente)
        i_total = imp * (irr_target / 1000.0) * num_strings_parallel

        # Si no hay sol, V e I son 0 (o cercanos a 0, V cae rápido sin luz)
        if irr_target < 1:
            v_string = 0
            i_total = 0

        self._attr_native_value = round(total_power, 2)
        self._attr_extra_state_attributes = {
            "irradiancia_referencia": round(irr_ref, 1),
            "irradiancia_incidente_estimada": round(irr_target, 1),
            "factor_transposicion": round(geometric_factor, 3),
            "temperatura_celula": round(t_cell, 1),
            "temperatura_ambiente": round(t_amb, 1),
            "factor_perdida_termica": round(temp_factor_power, 3),
            "sun_azimuth": round(sun_az, 1),
            "sun_elevation": round(sun_el, 1),
            "panel_model": self._panel_data.get("name"),
            "voltaje_total_estimado": round(v_string, 1),
            "corriente_total_estimada": round(i_total, 2)
        }

        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Suscribirse a actualizaciones."""
        entities = ["sun.sun", self._config.get(CONF_REF_SENSOR), self._config.get(CONF_TEMP_SENSOR)]
        if self._config.get(CONF_WIND_SENSOR):
            entities.append(self._config.get(CONF_WIND_SENSOR))
            
        self.async_on_remove(
            async_track_state_change_event(self.hass, entities, self._update_logic)
        )
        # Primera actualización
        self._update_logic()