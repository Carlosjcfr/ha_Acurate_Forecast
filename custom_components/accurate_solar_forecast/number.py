import logging
from homeassistant.components.number import NumberEntity, NumberDeviceClass, NumberMode
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN, CONF_STRING_NAME, CONF_TILT, CONF_AZIMUTH, CONF_SENSOR_GROUP_NAME

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Accurate Solar Forecast number entities."""
    
    if CONF_STRING_NAME in config_entry.data:
        # It's a String Entry
        async_add_entities([
            SolarStringTiltNumber(hass, config_entry),
            SolarStringAzimuthNumber(hass, config_entry)
        ])

class SolarStringNumberEntity(NumberEntity):
    """Base class for Solar String numbers."""
    
    def __init__(self, hass, config_entry):
        self.hass = hass
        self._config_entry = config_entry
        self._data = config_entry.data
        self._string_name = self._data.get(CONF_STRING_NAME)
        self._attr_has_entity_name = True

    @property
    def device_info(self):
        """Return device info linked to the String."""
        # Baseline identifier
        string_id = f"str_{self._string_name.lower().replace(' ', '_')}"
        device_identifiers = {(DOMAIN, string_id)}
        
        # Try to link to Real Production Sensor's device if configured
        from .const import CONF_REAL_PRODUCTION_SENSOR
        from homeassistant.helpers import device_registry as dr, entity_registry as er
        
        real_sensor_id = self._data.get(CONF_REAL_PRODUCTION_SENSOR)
        if real_sensor_id:
             ent_reg = er.async_get(self.hass)
             entity_entry = ent_reg.async_get(real_sensor_id)
             if entity_entry and entity_entry.device_id:
                 dev_reg = dr.async_get(self.hass)
                 device = dev_reg.async_get(entity_entry.device_id)
                 if device:
                     device_identifiers = device.identifiers

        return DeviceInfo(
            identifiers=device_identifiers
        )

class SolarStringTiltNumber(SolarStringNumberEntity):
    """Number entity for controlling Panel Tilt."""
    
    _attr_name = "Inclinación"
    _attr_native_min_value = 0
    _attr_native_max_value = 90
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "°"
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:angle-acute"

    def __init__(self, hass, config_entry):
        super().__init__(hass, config_entry)
        self._attr_unique_id = f"str_{self._string_name.lower().replace(' ', '_')}_tilt"
        self._attr_native_value = self._data.get(CONF_TILT, 0)

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        self._attr_native_value = value
        
        # Update Config Entry
        new_data = self._config_entry.data.copy()
        new_data[CONF_TILT] = value
        
        self.hass.config_entries.async_update_entry(self._config_entry, data=new_data)
        # Reload entry to propagate changes to sensor
        await self.hass.config_entries.async_reload(self._config_entry.entry_id)

class SolarStringAzimuthNumber(SolarStringNumberEntity):
    """Number entity for controlling Panel Azimuth."""
    
    _attr_name = "Orientación"
    _attr_native_min_value = 0
    _attr_native_max_value = 360
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "°"
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:compass"

    def __init__(self, hass, config_entry):
        super().__init__(hass, config_entry)
        self._attr_unique_id = f"str_{self._string_name.lower().replace(' ', '_')}_azimuth"
        self._attr_native_value = self._data.get(CONF_AZIMUTH, 180)

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        self._attr_native_value = value
        
        # Update Config Entry
        new_data = self._config_entry.data.copy()
        new_data[CONF_AZIMUTH] = value
        
        self.hass.config_entries.async_update_entry(self._config_entry, data=new_data)
        # Reload entry to propagate changes to sensor
        await self.hass.config_entries.async_reload(self._config_entry.entry_id)
