import math
import logging
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfPower, UnitOfTemperature, UnitOfSpeed
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.entity import DeviceInfo
from .const import *

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Accurate Solar Forecast sensors from a config entry."""
    db = hass.data[DOMAIN]["db"] # DB is assumed to be loaded in __init__
    
    # CASE 1: SENSOR GROUP (GROUP OF SENSORS)
    # CASE 1: SENSOR GROUP (GROUP OF SENSORS)
    if CONF_SENSOR_GROUP_NAME in config_entry.data:
        # Sensor Groups act as data containers for logical linking.
        # We do NOT create proxy entities to avoid duplication.
        # The data is already available in the DB for other components (Strings) to use.
        return

    # CASE 2: SOLAR STRING (POWER PREDICTION)
    elif CONF_STRING_NAME in config_entry.data:
        # We need to look up the Sensor Group data!
        # The string entry has 'selected_sensor_group' (which is the name/ID in DB)
        # However, to be robust, we should probably look up the CONFIG ENTRY of the sensor group?
        # OR just use the DB since the sensors are entities in HA anyway.
        # Let's use the DB to get the entity IDs associated with that group name.
        
        group_name = config_entry.data.get("selected_sensor_group")
        # In this implementation, the value stored was the Name (key in DB dict was name-based id)
        # But wait, config_flow list_sensor_groups returned {id: name}. SelectSelector returns the KEY (id).
        # So group_name is actually the group_id.
        
        sensor_group_data = db.get_sensor_group(group_name)
        
        if sensor_group_data:
            async_add_entities([SolarStringSensor(hass, config_entry.data, db, sensor_group_data)], update_before_add=True)
        else:
            _LOGGER.error(f"Sensor group '{group_name}' not found in DB for string {config_entry.title}")





class SolarStringSensor(SensorEntity):
    def __init__(self, hass, config_entry_data, db, sensor_group_data):
        self.hass = hass
        self._config = config_entry_data
        self._db = db
        self._sensor_group = sensor_group_data
        
        # Recuperar datos del modelo desde la DB usando el nombre
        model_name = self._config.get(CONF_PANEL_MODEL)
        self._panel_data = None
        if db and db.data:
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

        # Link to the Sensor Group Device? Or create its own device?
        # Strings are virtual, maybe its own device or no device (just entity).
        # Let's give it a device so it looks nice in UI.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=self._attr_name,
            manufacturer=self._panel_data.get("brand", "Generic") if self._panel_data else "Generic",
            model=model_name,
            via_device=(DOMAIN, sensor_group_data.get(CONF_SENSOR_GROUP_NAME)) # Logically linked
        )

    @property
    def check_config(self):
        return self._panel_data is not None and self._sensor_group is not None

    def get_float_state(self, entity_id, default=0.0):
        if not entity_id:
            return default
        state = self.hass.states.get(entity_id)
        if state and state.state not in ["unavailable", "unknown"]:
            try:
                return float(state.state)
            except ValueError:
                pass
        return default

    def calculate_cos_incidence(self, sun_az, sun_el, panel_az, panel_tilt):
        """Calcula el coseno del ángulo de incidencia."""
        sol_zenith_rad = math.radians(90 - sun_el)
        sol_az_rad = math.radians(sun_az)
        panel_tilt_rad = math.radians(panel_tilt)
        panel_az_rad = math.radians(panel_az)

        cos_theta = (math.cos(sol_zenith_rad) * math.cos(panel_tilt_rad)) + \
                    (math.sin(sol_zenith_rad) * math.sin(panel_tilt_rad) * math.cos(sol_az_rad - panel_az_rad))
        
        return max(0, cos_theta)

    @callback
    def _update_logic(self, event=None):
        if not self.check_config:
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

        # 2. Datos del Sensor de Referencia (DESDE EL GRUPO DE SENSORES)
        ref_sensor = self._sensor_group.get(CONF_REF_SENSOR)
        irr_ref = self.get_float_state(ref_sensor, 0.0)
        
        # 3. Datos Ambientales (DESDE EL GRUPO DE SENSORES)
        temp_sensor = self._sensor_group.get(CONF_TEMP_SENSOR)
        t_amb = self.get_float_state(temp_sensor, 25.0)
        
        wind_sensor = self._sensor_group.get(CONF_WIND_SENSOR)
        wind_speed = 1.0 
        if wind_sensor:
            wind_speed = self.get_float_state(wind_sensor, 1.0)
            
        # Panel Temp (Si existe en el grupo)
        # ... logic not implemented fully in previous version but ready here

        # 4. Cálculos Geométricos para Transposición
        target_az = self._config.get(CONF_AZIMUTH)
        target_tilt = self._config.get(CONF_TILT)
        cos_theta_target = self.calculate_cos_incidence(sun_az, sun_el, target_az, target_tilt)

        # Sensor Referencia (GEOMETRÍA DESDE EL GRUPO)
        ref_az = self._sensor_group.get(CONF_REF_ORIENTATION)
        ref_tilt = self._sensor_group.get(CONF_REF_TILT)
        cos_theta_ref = self.calculate_cos_incidence(sun_az, sun_el, ref_az, ref_tilt)

        # Transposición de Irradiancia
        if cos_theta_ref < 0.05:
            geometric_factor = 0 if irr_ref > 10 else 1 
        else:
            geometric_factor = cos_theta_target / cos_theta_ref
        
        irr_target = irr_ref * geometric_factor

        # 5. Modelo Térmico
        noct = self._panel_data.get("noct", 45)
        t_cell = t_amb + (irr_target / 800) * (noct - 20)

        # 6. Cálculo de Potencia DC
        p_stc = self._panel_data.get("p_stc", 400)
        gamma = self._panel_data.get("gamma", -0.4) / 100.0
        num_panels_series = self._config.get(CONF_NUM_PANELS, 1)
        num_strings_parallel = self._config.get(CONF_NUM_STRINGS, 1)

        temp_diff = t_cell - 25
        temp_factor_power = 1 + (gamma * temp_diff)
        
        power_unit = p_stc * (irr_target / 1000.0) * temp_factor_power
        total_panels = num_panels_series * num_strings_parallel
        total_power = max(0, power_unit * total_panels)

        # VOLTAJE E INTENSIDAD (Estimación)
        vmp = self._panel_data.get("vmp", 30.0)
        imp = self._panel_data.get("imp", 10.0)
        
        v_string = vmp * num_panels_series * temp_factor_power
        i_total = imp * (irr_target / 1000.0) * num_strings_parallel

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
            "voltaje_total_estimado": round(v_string, 1),
            "corriente_total_estimada": round(i_total, 2)
        }
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Suscribirse a actualizaciones."""
        # Get entities from the sensor group dict
        entities = ["sun.sun", self._sensor_group.get(CONF_REF_SENSOR), self._sensor_group.get(CONF_TEMP_SENSOR)]
        if self._sensor_group.get(CONF_WIND_SENSOR):
            entities.append(self._sensor_group.get(CONF_WIND_SENSOR))
            
        self.async_on_remove(
            async_track_state_change_event(self.hass, entities, self._update_logic)
        )
        self._update_logic()