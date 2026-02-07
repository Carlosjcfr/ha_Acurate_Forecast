import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import *
from .pv_database import PVDatabase

class AccurateForecastFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._db = None

    async def async_step_user(self, user_input=None):
        """Menú Principal: ¿Qué quieres hacer?"""
        self._db = self.hass.data[DOMAIN]["db"]
        
        return self.async_show_menu(
            step_id="user",
            menu_options=["add_string", "add_pv_model"]
        )

    # --- OPCIÓN A: AÑADIR MODELO A LA BASE DE DATOS ---
    async def async_step_add_pv_model(self, user_input=None):
        errors = {}
        if user_input is not None:
            # Guardar en la DB
            await self._db.add_model(
                user_input["name"],
                user_input["p_stc"],
                user_input["gamma"],
                user_input["noct"]
            )
            # Volver al menú o cerrar
            return self.async_create_entry(title="Modelo Guardado", data={})

        schema = vol.Schema({
            vol.Required("name"): str,
            vol.Required("p_stc", default=400): vol.Coerce(float),
            vol.Required("gamma", default=-0.35): vol.Coerce(float), # %/C
            vol.Required("noct", default=45): vol.Coerce(float),
        })

        return self.async_show_form(step_id="add_pv_model", data_schema=schema, errors=errors)

    # --- OPCIÓN B: CREAR UN STRING (SENSOR) ---
    async def async_step_add_string(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_STRING_NAME], 
                data=user_input
            )

        # Obtener lista de modelos de la DB para el desplegable
        models_list = self._db.list_models()

        schema = vol.Schema({
            vol.Required(CONF_STRING_NAME): str,
            # Selector de Modelo (desde nuestra DB)
            vol.Required(CONF_PANEL_MODEL): selector.SelectSelector(
                selector.SelectSelectorConfig(options=list(models_list.values()), mode="dropdown")
            ),
            vol.Required(CONF_NUM_PANELS, default=1): int,
            
            # Geometría del String Nuevo
            vol.Required(CONF_AZIMUTH, default=180): vol.All(vol.Coerce(float), vol.Range(min=0, max=360)),
            vol.Required(CONF_TILT, default=30): vol.All(vol.Coerce(float), vol.Range(min=0, max=90)),

            # Datos del Sensor Fuente (Origen)
            vol.Required(CONF_REF_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(CONF_REF_AZIMUTH, default=180): vol.Coerce(float),
            vol.Required(CONF_REF_TILT, default=0): vol.Coerce(float), # 0 = Horizontal

            # Sensores Ambientales
            vol.Required(CONF_TEMP_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
            ),
            vol.Optional(CONF_WIND_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
        })

        return self.async_show_form(step_id="add_string", data_schema=schema)