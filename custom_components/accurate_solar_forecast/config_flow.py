import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import *
from .pv_database import PVDatabase

class AccurateForecastFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._db = None
        self.selected_brand = None
        self.string_data = {}

    async def async_step_user(self, user_input=None):
        """Menú Principal: ¿Qué quieres hacer?"""
        # Asegurar que DOMAIN existe en hass.data
        self.hass.data.setdefault(DOMAIN, {})

        # Inicializar la base de datos si no existe
        if "db" not in self.hass.data[DOMAIN]:
            self._db = PVDatabase(self.hass)
            await self._db.async_load()
            self.hass.data[DOMAIN]["db"] = self._db
        else:
            self._db = self.hass.data[DOMAIN]["db"]
        
        return self.async_show_menu(
            step_id="user",
            menu_options=["add_pv_model", "add_irradiance_sensor", "add_string"]
        )

    # --- OPCIÓN A: AÑADIR MODELO A LA BASE DE DATOS ---
    async def async_step_add_pv_model(self, user_input=None):
        errors = {}
        if user_input is not None:
            # Guardar en la DB
            await self._db.add_model(
                user_input["name"],
                user_input[CONF_BRAND],
                user_input["p_stc"],
                user_input["gamma"],
                user_input["noct"],
                user_input[CONF_VOC],
                user_input[CONF_ISC],
                user_input[CONF_VMP],
                user_input[CONF_IMP]
            )
            # Volver al menú o cerrar
            return self.async_create_entry(title=user_input["name"], data={})

        # Get existing brands to populate the list
        brands_list = self._db.list_brands()

        schema = vol.Schema({
            vol.Required("name"): str,
            # Seleccionable de Marca con opción de escribir nueva
            vol.Required(CONF_BRAND): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=brands_list, 
                    custom_value=True, 
                    mode="dropdown"
                )
            ),
            vol.Required("p_stc", default=400): vol.Coerce(float),
            vol.Required("gamma", default=-0.35): vol.Coerce(float), # %/C
            vol.Required("noct", default=45): vol.Coerce(float),
            vol.Required(CONF_VOC, default=50.0): vol.Coerce(float),
            vol.Required(CONF_ISC, default=11.0): vol.Coerce(float),
            vol.Required(CONF_VMP, default=41.0): vol.Coerce(float),
            vol.Required(CONF_IMP, default=10.0): vol.Coerce(float),
        })

        return self.async_show_form(step_id="add_pv_model", data_schema=schema, errors=errors)

    # --- OPCIÓN C: AÑADIR SENSOR DE IRRADIANCIA ---
    async def async_step_add_irradiance_sensor(self, user_input=None):
        if user_input is not None:
            # Create entry for irradiance sensor
            return self.async_create_entry(
                title=user_input["name"],
                data=user_input
            )

        schema = vol.Schema({
            vol.Required("name"): str,
            vol.Required("irradiance_sensor"): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor", 
                    device_class="irradiance"
                )
            ),
            vol.Optional(CONF_TEMP_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
            ),
            vol.Optional(CONF_WIND_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="wind_speed")
            ),
        })

        return self.async_show_form(step_id="add_irradiance_sensor", data_schema=schema)

    # --- OPCIÓN B: CREAR UN STRING (SENSOR) - PASO 1: SELECCIONAR MARCA ---
    async def async_step_add_string(self, user_input=None):
        if user_input is not None:
            self.selected_brand = user_input[CONF_BRAND]
            return await self.async_step_add_string_details()

        brands_list = self._db.list_brands()
        
        schema = vol.Schema({
            vol.Required(CONF_BRAND): selector.SelectSelector(
                selector.SelectSelectorConfig(options=brands_list, mode="dropdown")
            )
        })

        return self.async_show_form(step_id="add_string", data_schema=schema)

    # --- PASO 2: DETALLES DEL STRING (FILTRADO POR MARCA) ---
    async def async_step_add_string_details(self, user_input=None):
        if user_input is not None:
            self.string_data = user_input
            return await self.async_step_ref_sensor()

        # Gets models for the selected brand
        models_filtered = self._db.list_models_by_brand(self.selected_brand)

        schema = vol.Schema({
            vol.Required(CONF_STRING_NAME): str,
            # Selector de Modelo FILTRADO
            vol.Required(CONF_PANEL_MODEL): selector.SelectSelector(
                selector.SelectSelectorConfig(options=list(models_filtered.values()), mode="dropdown")
            ),
            vol.Required(CONF_NUM_PANELS, default=1): int,
            vol.Required(CONF_NUM_STRINGS, default=1): int,
            
            # Geometría del String Nuevo
            vol.Required(CONF_AZIMUTH, default=180): vol.All(vol.Coerce(float), vol.Range(min=0, max=360)),
            vol.Required(CONF_TILT, default=30): vol.All(vol.Coerce(float), vol.Range(min=0, max=90)),
        })

        return self.async_show_form(step_id="add_string_details", data_schema=schema)

    # --- PASO 3: SENSORES DE REFERENCIA Y AMBIENTALES ---
    async def async_step_ref_sensor(self, user_input=None):
        if user_input is not None:
            # Merge data
            full_data = {**self.string_data, **user_input}
            return self.async_create_entry(
                title=self.string_data[CONF_STRING_NAME], 
                data=full_data
            )
            
        schema = vol.Schema({
            # Datos del Sensor Fuente (Origen)
            vol.Required(CONF_REF_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor", 
                    device_class=["irradiance", "power"]
                )
            ),
            vol.Required(CONF_REF_AZIMUTH, default=180): vol.Coerce(float),
            vol.Required(CONF_REF_TILT, default=0): vol.Coerce(float), # 0 = Horizontal

            # Sensores Ambientales
            vol.Required(CONF_TEMP_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
            ),
            vol.Optional(CONF_WIND_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="wind_speed")
            ),
        })

        return self.async_show_form(step_id="ref_sensor", data_schema=schema)