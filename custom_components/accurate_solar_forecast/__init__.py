from homeassistant.core import HomeAssistant
from .const import DOMAIN, CONF_SENSOR_GROUP_NAME
from .pv_database import PVDatabase
import logging

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry):
    # Cargar la DB y ponerla disponible globalmente
    if DOMAIN not in hass.data:
        db = PVDatabase(hass)
        await db.async_load()
        hass.data[DOMAIN] = {"db": db}
    else:
        # Ensure older entries get the DB reference if hot-reloading
        if "db" not in hass.data[DOMAIN]:
             db = PVDatabase(hass)
             await db.async_load()
             hass.data[DOMAIN]["db"] = db

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_setup(hass: HomeAssistant, config):
    # Inicialización global
    hass.data.setdefault(DOMAIN, {})
    if "db" not in hass.data[DOMAIN]:
        db = PVDatabase(hass)
        await db.async_load()
        hass.data[DOMAIN]["db"] = db
    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

async def async_remove_entry(hass: HomeAssistant, entry) -> None:
    """Handle removal of an entry."""
    # This is called when the user clicks 'Delete' on the Integration card.
    if DOMAIN in hass.data and "db" in hass.data[DOMAIN]:
        db = hass.data[DOMAIN]["db"]
        
        # Case A: Sensor Group
        if CONF_SENSOR_GROUP_NAME in entry.data:
            # The key in DB is usually name.lower().replace(" ", "_")
            group_name = entry.data[CONF_SENSOR_GROUP_NAME]
            group_id = group_name.lower().replace(" ", "_")
            _LOGGER.info(f"Removing Sensor Group from DB: {group_id}")
            result = db.delete_sensor_group(group_id)
            if result:
               await result
               
        # Case B: String (Does it have a DB entry? No, strings are just ConfigEntries)
        # Strings use data from DB (models and sensor groups) but are not stored in DB themselves
        # EXCEPT if we decide to track them there. Current architecture suggests Strings are purely ConfigEntries.
        # But wait, PVDatabase DOES have 'models'. 
        return