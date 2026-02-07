from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .pv_database import PVDatabase

PLATFORMS = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry):
    # Cargar la DB y ponerla disponible globalmente
    if DOMAIN not in hass.data:
        db = PVDatabase(hass)
        await db.async_load()
        hass.data[DOMAIN] = {"db": db}
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_setup(hass: HomeAssistant, config):
    # Inicialización global
    if DOMAIN not in hass.data:
        db = PVDatabase(hass)
        await db.async_load()
        hass.data[DOMAIN] = {"db": db}
    return True