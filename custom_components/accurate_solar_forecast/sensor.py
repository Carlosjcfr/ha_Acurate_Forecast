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
    def __init__(self, hass, config, db):
        self.hass = hass
        self._config = config
        self._db = db
        
        # Recuperar datos del modelo desde la DB usando el nombre
        model_name = config.get(CONF_PANEL_MODEL)
        # Búsqueda inversa simple (nombre -> datos)
        self._panel_data = next((v for k, v in db.data.items() if v["name"] == model_name), None)
        
        self._attr_name = config.get(CONF_STRING_NAME)
        self._attr_unique_id = f"str_{config.get(CONF_STRING_NAME).lower().replace(' ', '_')}"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT

    def get_solar_geometry(self):
        """Calcula Azimut y Elevación del sol usando sun.sun"""
        sun_state = self.hass.states.get("sun.sun")
        if not sun_state:
            return 0, 0
        
        # HA da azimuth (0=Norte, 90=Este) y elevation
        azimuth = float(sun_state.attributes.get("azimuth", 180))
        elevation = float(sun_state.attributes.get("elevation", 0))
        return azimuth, elevation

    def calculate_incidence_angle(self, sun_az, sun_el, panel_az, panel_tilt):
        """Calcula el coseno del ángulo de incidencia."""
        # Convertir a radianes
        s_az_rad = math.radians(sun_az)
        s_el_rad = math.radians(sun_el)
        p_az_rad = math.radians(panel_az)
        p_tilt_rad = math.radians(panel_tilt)

        # Ángulo cenital solar (90 - elevacion)
        zenith_rad = math.radians(90 - sun_el)

        # Fórmula AOI
        # cos(θ) = cos(θ_zenith)*cos(θ_tilt) + sin(θ_zenith)*sin(θ_tilt)*cos(Az_sun - Az_panel)
        cos_theta = (math.cos(zenith_rad) * math.cos(p_tilt_rad)) + \
                    (math.sin(zenith_rad) * math.sin(p_tilt_rad) * math.cos(s_az_rad - p_az_rad))
        
        return max(0, cos_theta) # No aceptamos valores negativos (sol detrás del panel)

    @callback
    def _update_logic(self, event=None):
        # 1. Obtener Irradiancia Base
        ref_entity = self._config.get(CONF_REF_SENSOR)
        irr_state = self.hass.states.get(ref_entity)
        
        if not irr_state or irr_state.state in ["unavailable", "unknown"]:
            self._attr_native_value = 0
            return

        irr_raw = float(irr_state.state) # W/m2 en el sensor origen

        # 2. Calcular Geometría Solar
        sun_az, sun_el = self.get_solar_geometry()
        
        if sun_el <= 0: # Es de noche
            self._attr_native_value = 0
            self.async_write_ha_state()
            return

        # 3. Calcular Factor de Transposición
        # AOI del Sensor Origen
        cos_theta_ref = self.calculate_incidence_angle(
            sun_az, sun_el, 
            self._config.get(CONF_REF_AZIMUTH), 
            self._config.get(CONF_REF_TILT)
        )
        
        # AOI del String Destino
        cos_theta_target = self.calculate_incidence_angle(
            sun_az, sun_el, 
            self._config.get(CONF_AZIMUTH), 
            self._config.get(CONF_TILT)
        )

        # Evitar división por cero si el sensor origen está en sombra extrema (o mal configurado)
        if cos_theta_ref < 0.1: 
            # Si el sensor de referencia no ve el sol, asumimos irradiancia difusa pura 
            # o que la medición no es fiable para transponer direct beam.
            geometric_factor = 1 # Fallback conservador
        else:
            geometric_factor = cos_theta_target / cos_theta_ref

        # Irradiancia Estimada en el plano del String
        irr_target = irr_raw * geometric_factor

        # 4. Calcular Temperatura de Célula (Lógica Térmica)
        # ... (Aquí va la lógica térmica que hicimos antes: Faiman / NOCT) ...
        # Usaremos irr_target para el calentamiento
        
        # [CÓDIGO DE Tº y POTENCIA FINAL DE LOS PASOS ANTERIORES AQUÍ]
        # P_final = P_stc * Num_Panels * (irr_target / 1000) * Factor_Temp
        
        self._attr_native_value = round(p_final, 1)
        self._attr_extra_state_attributes = {
            "irradiancia_origen": irr_raw,
            "irradiancia_transpuesta": round(irr_target, 1),
            "factor_geometrico": round(geometric_factor, 2),
            "sun_azimuth": sun_az,
            "sun_elevation": sun_el
        }
        
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        # Suscribirse a cambios del sol y sensores
        entities = [
            "sun.sun",
            self._config.get(CONF_REF_SENSOR),
            self._config.get(CONF_TEMP_SENSOR)
        ]
        self.async_on_remove(
            async_track_state_change_event(self.hass, entities, self._update_logic)
        )