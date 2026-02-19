import logging
from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN, CONF_STRING_NAME

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Accurate Solar Forecast select entities."""
    if CONF_STRING_NAME in config_entry.data:
        # Placeholder for 'Cubierta' select if we want to implement it later
        # For now, maybe just a dummy or simple preset selector?
        # User asked for "Cubierta".
        pass

# We will implement this later if needed or if user enables cover management again.
