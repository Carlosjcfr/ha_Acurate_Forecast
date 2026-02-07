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

async def async_unload_entry(hass: HomeAssistant, entry):
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

async def async_remove_entry(hass: HomeAssistant, entry) -> None:
    """Handle removal of an entry."""
    if DOMAIN in hass.data and "db" in hass.data[DOMAIN]:
        db = hass.data[DOMAIN]["db"]
        # Reconstruct model_id from title
        model_id = entry.title.lower().replace(" ", "_")
        # Try to delete it
        result = db.delete_model(model_id)
        if result:
            await result