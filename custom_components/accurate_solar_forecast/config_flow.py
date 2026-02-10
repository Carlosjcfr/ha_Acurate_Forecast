import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import *
from .pv_database import PVDatabase

class AccurateForecastFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    
    

    def __init__(self):
        self._db = None
        
        # State Management
        self.selected_item_id = None     # ID of the item being edited/deleted
        self.temp_data = {}              # Temporary storage for multi-step flows
        
        # Branch Handling
        # Branch 1: PV Models
        # Branch 2: Strings
        # Branch 3: Sensor Groups
        
    async def async_step_user(self, user_input=None):
        """Menú Principal: ¿Qué quieres gestionar?"""
        # Asegurar que DOMAIN existe en hass.data
        self.hass.data.setdefault(DOMAIN, {})
        # Reset generic temporary data to ensure clean state
        self.temp_data = {}

        # Inicializar la base de datos si no existe
        if "db" not in self.hass.data[DOMAIN]:
            self._db = PVDatabase(self.hass)
            await self._db.async_load()
            self.hass.data[DOMAIN]["db"] = self._db
        else:
            self._db = self.hass.data[DOMAIN]["db"]
        
        return self.async_show_menu(
            step_id="user",
            menu_options=["menu_pv_models", "menu_strings", "menu_sensor_groups"]
        )

    # =================================================================================
    # BRANCH 1: PV MODELS (Datos Puros - Mantenemos Create, Edit, Delete)
    # =================================================================================
    async def async_step_menu_pv_models(self, user_input=None):
        """Submenú para Módulos FV."""
        return self.async_show_menu(
            step_id="menu_pv_models",
            menu_options=["pv_model_create", "pv_model_edit_select"]
        )

    # 1.1 CREATE PV MODEL
    async def async_step_pv_model_create(self, user_input=None):
        """Crear un nuevo modelo."""
        errors = {}
        if user_input is not None:
             # Guardar en DB
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
            return await self.async_step_pv_model_success()

        return self._show_pv_model_form("pv_model_create", errors)

    # 1.2 EDIT PV MODEL (Select -> Form)
    async def async_step_pv_model_edit_select(self, user_input=None):
        if user_input is not None:
             self.selected_item_id = user_input["selected_model"]
             return await self.async_step_pv_model_edit_form()
             
        return self._show_model_selector("pv_model_edit_select")

     async def async_step_pv_model_edit_form(self, user_input=None):
        if user_input is not None:
            # Update (Overwriting add_model handles update if ID matches, but ID logic needs care.
            # Here we assume user might change name, creating new ID? 
            # Ideally we keep ID constant or allow full overwrite. 
            # For simplicity: Delete old, Create new OR Update fields.
            # DB add_model uses name as ID source. If name changes -> New Entry.
            # Let's keep it simple: Add/Update based on name.
            
            # If name changed, we should probably delete old one? 
            # This is complex. Let's just update for now.
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
            return await self.async_step_pv_model_success()

        # Load Data
        # We need to find the model data by name/id
        # The selector returned the ID (name based key)
        model_data = self._db.get_model(self.selected_item_id)
        return self._show_pv_model_form("pv_model_edit_form", {}, default_data=model_data)

    # 1.3 SUCCESS & LOOP (Menu intermedio)
    async def async_step_pv_model_success(self, user_input=None):
        """Menu intermedio tras crear/editar modelo."""
        return self.async_show_menu(
            step_id="pv_model_success",
            menu_options=["pv_model_create", "pv_model_finish"]
        )

    async def async_step_pv_model_finish(self, user_input=None):
        """Finalizar el flujo de modelos (sin crear entrada en HA, solo guardando DB)."""
        return self.async_abort(reason="models_saved")


    # Helper: Model Form
    def _show_pv_model_form(self, step_id, errors, default_data=None):
        if default_data is None: default_data = {}
        
        brands_list = self._db.list_brands()
        schema = vol.Schema({
            vol.Required("name", default=default_data.get("name", vol.UNDEFINED)): str,
            vol.Required(CONF_BRAND, default=default_data.get("brand", vol.UNDEFINED)): selector.SelectSelector(
                selector.SelectSelectorConfig(options=brands_list, custom_value=True, mode="dropdown")
            ),
            vol.Required("p_stc", default=default_data.get("p_stc", vol.UNDEFINED)): vol.Coerce(float),
            vol.Required("gamma", default=default_data.get("gamma", vol.UNDEFINED)): vol.Coerce(float),
            vol.Required("noct", default=default_data.get("noct", vol.UNDEFINED)): vol.Coerce(float),
            vol.Required(CONF_VOC, default=default_data.get("voc", vol.UNDEFINED)): vol.Coerce(float),
            vol.Required(CONF_ISC, default=default_data.get("isc", vol.UNDEFINED)): vol.Coerce(float),
            vol.Required(CONF_VMP, default=default_data.get("vmp", vol.UNDEFINED)): vol.Coerce(float),
            vol.Required(CONF_IMP, default=default_data.get("imp", vol.UNDEFINED)): vol.Coerce(float),
        })
        return self.async_show_form(step_id=step_id, data_schema=schema, errors=errors)

    # Helper: Model Selector
    def _show_model_selector(self, step_id):
        models = self._db.list_models() # {id: name}
        if not models:
             return self.async_abort(reason="no_models_available")
        
        schema = vol.Schema({
            vol.Required("selected_model"): selector.SelectSelector(
                selector.SelectSelectorConfig(options=list(models.keys()), mode="dropdown")
            )
        })
        return self.async_show_form(step_id=step_id, data_schema=schema)

    # =================================================================================
    # BRANCH 2: SENSOR GROUPS (Integraciones - Create & Edit Only)
    # =================================================================================
    async def async_step_menu_sensor_groups(self, user_input=None):
        return self.async_show_menu(
            step_id="menu_sensor_groups",
             # Removed 'delete' option as per user request to use native HA delete
            menu_options=["sensor_group_create", "sensor_group_edit_select"]
        )

    # 2.1 CREATE SENSOR GROUP
    async def async_step_sensor_group_create(self, user_input=None):
         errors = {}
         if user_input is not None:
            name = user_input[CONF_SENSOR_GROUP_NAME]
            # Save to DB
            await self._db.add_sensor_group(
                name,
                user_input[CONF_REF_SENSOR],
                user_input[CONF_TEMP_SENSOR],
                user_input.get(CONF_TEMP_PANEL_SENSOR),
                user_input.get(CONF_WIND_SENSOR),
                user_input[CONF_REF_TILT],
                user_input[CONF_REF_ORIENTATION]
            )
            # Create HA Device
            return self.async_create_entry(title=name, data=user_input)
            
         return self._show_sensor_group_form("sensor_group_create", errors)

    # 2.2 EDIT SENSOR GROUP (Update DB only)
    async def async_step_sensor_group_edit_select(self, user_input=None):
        if user_input is not None:
             self.selected_item_id = user_input["selected_group"]
             return await self.async_step_sensor_group_edit_form()

        groups = self._db.list_sensor_groups()
        if not groups:
             return self.async_abort(reason="no_sensor_groups")

        schema = vol.Schema({
            vol.Required("selected_group"): selector.SelectSelector(
                selector.SelectSelectorConfig(options=list(groups.keys()), mode="dropdown")
            )
        })
        return self.async_show_form(step_id="sensor_group_edit_select", data_schema=schema)

    async def async_step_sensor_group_edit_form(self, user_input=None):
        if user_input is not None:
             name = user_input[CONF_SENSOR_GROUP_NAME]
             await self._db.add_sensor_group(
                name,
                user_input[CONF_REF_SENSOR],
                user_input[CONF_TEMP_SENSOR],
                user_input.get(CONF_TEMP_PANEL_SENSOR),
                user_input.get(CONF_WIND_SENSOR),
                user_input[CONF_REF_TILT],
                user_input[CONF_REF_ORIENTATION]
            )
             return self.async_create_entry(title=f"Updated Group: {name}", data={})

        group_data = self._db.get_sensor_group(self.selected_item_id)
        return self._show_sensor_group_form("sensor_group_edit_form", {}, default_data=group_data)

    # Helper: Sensor Group Form
    def _show_sensor_group_form(self, step_id, errors, default_data=None):
        if default_data is None: default_data = {}
        
        # Valid Sensors
        valid_irradiance_sensors = []
        for state in self.hass.states.async_all("sensor"):
            attributes = state.attributes
            if (attributes.get("device_class") == "irradiance" or 
                attributes.get("unit_of_measurement") in ["W/m²", "W/m2"]):
                valid_irradiance_sensors.append(state.entity_id)
        valid_irradiance_sensors.sort()

        schema = vol.Schema({
            vol.Required(CONF_SENSOR_GROUP_NAME, default=default_data.get(CONF_SENSOR_GROUP_NAME, "")): str,
            vol.Required(CONF_REF_SENSOR, default=default_data.get(CONF_REF_SENSOR, vol.UNDEFINED)): selector.EntitySelector(
                selector.EntitySelectorConfig(include_entities=valid_irradiance_sensors)
            ),
            vol.Required(CONF_REF_TILT, default=default_data.get(CONF_REF_TILT, 0)): vol.All(vol.Coerce(float), vol.Range(min=0, max=90)),
            vol.Required(CONF_REF_ORIENTATION, default=default_data.get(CONF_REF_ORIENTATION, 180)): vol.All(vol.Coerce(float), vol.Range(min=0, max=360)),
            vol.Required(CONF_TEMP_SENSOR, default=default_data.get(CONF_TEMP_SENSOR, vol.UNDEFINED)): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
            ),
            vol.Optional(CONF_TEMP_PANEL_SENSOR, default=default_data.get(CONF_TEMP_PANEL_SENSOR, vol.UNDEFINED)): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
            ),
            vol.Optional(CONF_WIND_SENSOR, default=default_data.get(CONF_WIND_SENSOR, vol.UNDEFINED)): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="wind_speed")
            ),
        })
        return self.async_show_form(step_id=step_id, data_schema=schema, errors=errors)

    # =================================================================================
    # BRANCH 3: STRINGS (Integraciones - Create & Edit Only)
    # =================================================================================
    async def async_step_menu_strings(self, user_input=None):
        return self.async_show_menu(
            step_id="menu_strings",
            # Removed delete, Edit String to be implemented later fully
            menu_options=["string_create_select_brand"] 
        )

    # 3.1 CREATE STRING - Step A: Select Brand & Group
    async def async_step_string_create_select_brand(self, user_input=None):
         if user_input is not None:
            self.temp_data = user_input
            return await self.async_step_string_create_details()

         brands_list = self._db.list_brands()
         sensor_groups = self._db.list_sensor_groups()
         
         if not sensor_groups:
             return self.async_abort(reason="no_sensor_groups_available")
         
         group_options = list(sensor_groups.keys())

         schema = vol.Schema({
            vol.Required(CONF_STRING_NAME): str,
            vol.Required("selected_sensor_group"): selector.SelectSelector(
                selector.SelectSelectorConfig(options=group_options, mode="dropdown")
            ),
            vol.Required(CONF_BRAND, default="Generic"): selector.SelectSelector(
                selector.SelectSelectorConfig(options=brands_list, mode="dropdown")
            )
        })
         return self.async_show_form(step_id="string_create_select_brand", data_schema=schema)

    # 3.1 CREATE STRING - Step B: Details
    async def async_step_string_create_details(self, user_input=None):
        if user_input is not None:
             final_data = {**self.temp_data, **user_input}
             return self.async_create_entry(
                title=self.temp_data[CONF_STRING_NAME], 
                data=final_data
            )
            
        selected_brand = self.temp_data[CONF_BRAND]
        models_filtered = self._db.list_models_by_brand(selected_brand)
        
        schema = vol.Schema({
            vol.Required(CONF_PANEL_MODEL): selector.SelectSelector(
                selector.SelectSelectorConfig(options=list(models_filtered.values()), mode="dropdown")
            ),
            vol.Required(CONF_NUM_PANELS, default=1): int,
            vol.Required(CONF_NUM_STRINGS, default=1): int,
            vol.Required(CONF_TILT, default=30): vol.All(vol.Coerce(float), vol.Range(min=0, max=90)),
            vol.Required(CONF_AZIMUTH, default=180): vol.All(vol.Coerce(float), vol.Range(min=0, max=360)),
        })
        return self.async_show_form(step_id="string_create_details", data_schema=schema)