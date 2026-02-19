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
        
        menu_options = ["menu_pv_models"]
        
        # Strings require a sensor group to be associated with
        if self._db.list_sensor_groups() and len(self._db.list_sensor_groups()) > 0:
            menu_options.append("menu_strings")
            
        menu_options.append("menu_sensor_groups")
        
        return self.async_show_menu(
            step_id="user",
            menu_options=menu_options
        )

    # =================================================================================
    # BRANCH 1: PV MODELS (Datos Puros - Mantenemos Create, Edit, Delete)
    # =================================================================================
    async def async_step_menu_pv_models(self, user_input=None):
        """Submenú para Módulos FV."""
        options = ["pv_model_create"]
        
        models = self._db.list_models()
        if models and len(models) > 0:
             options.append("pv_model_edit_select")
             
             # Check if there are models other than default to allow delete
             # Assuming 'default_450w' is the key for the default model
             deletable_models = [k for k in models.keys() if k != "default_450w"]
             if len(deletable_models) > 0:
                options.append("pv_model_delete_select")
             
        return self.async_show_menu(
            step_id="menu_pv_models",
            menu_options=options
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
        return self.async_abort(reason="pv_models_saved")


    # Helper: Model Form
    def _show_pv_model_form(self, step_id, errors, default_data=None):
        if default_data is None: default_data = {}
        
        brands_list = self._db.list_brands()
        schema = vol.Schema({
            vol.Required("name", default=default_data.get("name", vol.UNDEFINED)): str,
            vol.Required(CONF_BRAND, default=default_data.get("brand", vol.UNDEFINED)): selector.SelectSelector(
                selector.SelectSelectorConfig(options=brands_list, custom_value=True, mode="dropdown")
            ),
            vol.Required("p_stc", default=default_data.get("p_stc", vol.UNDEFINED)): vol.All(vol.Coerce(float), vol.Range(min=0.1)),
            vol.Required("gamma", default=default_data.get("gamma", vol.UNDEFINED)): vol.Coerce(float),
            vol.Required("noct", default=default_data.get("noct", vol.UNDEFINED)): vol.All(vol.Coerce(float), vol.Range(min=0, max=100)),
            vol.Required(CONF_VOC, default=default_data.get("voc", vol.UNDEFINED)): vol.All(vol.Coerce(float), vol.Range(min=0.1)),
            vol.Required(CONF_ISC, default=default_data.get("isc", vol.UNDEFINED)): vol.All(vol.Coerce(float), vol.Range(min=0.1)),
            vol.Required(CONF_VMP, default=default_data.get("vmp", vol.UNDEFINED)): vol.All(vol.Coerce(float), vol.Range(min=0.1)),
            vol.Required(CONF_IMP, default=default_data.get("imp", vol.UNDEFINED)): vol.All(vol.Coerce(float), vol.Range(min=0.1)),
        })
        return self.async_show_form(step_id=step_id, data_schema=schema, errors=errors)

    # 1.4 DELETE PV MODEL
    async def async_step_pv_model_delete_select(self, user_input=None):
        if user_input is not None:
             model_id = user_input["selected_model"]
             if model_id == "default_450w":
                 return self.async_abort(reason="cannot_delete_default")
             
             await self._db.delete_model(model_id)
             return self.async_create_entry(title=f"Deleted Model: {model_id}", data={})
             
        # Filter out default model from list if valid
        # Actually backend prevents it, but UI should also hide it or handle it?
        # Let's filter it out from the list to be user friendly
        models = self._db.list_models()
        if "default_450w" in models:
            del models["default_450w"]

        if not models:
             return self.async_abort(reason="no_models_available_to_delete")
        
        schema = vol.Schema({
            vol.Required("selected_model"): selector.SelectSelector(
                selector.SelectSelectorConfig(options=list(models.keys()), mode="dropdown")
            )
        })
        return self.async_show_form(step_id="pv_model_delete_select", data_schema=schema)

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
        # Explicitly reload DB to ensure freshness just in case
        if self._db:
             await self._db.async_load()

        # Optimization: If no groups, go straight to creation
        # We check the length explicitly to be robust
        groups = self._db.list_sensor_groups()
        if not groups or len(groups) == 0:
             return await self.async_step_sensor_group_create()

        options = ["sensor_group_create", "sensor_group_edit_select"]
        return self.async_show_menu(
            step_id="menu_sensor_groups",
            menu_options=options
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
                user_input[CONF_REF_ORIENTATION],
                user_input.get(CONF_WEATHER_ENTITY)
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
                user_input[CONF_REF_ORIENTATION],
                user_input.get(CONF_WEATHER_ENTITY)
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

        # Prepare defaults, handling None values correctly by converting to vol.UNDEFINED
        def get_default(key, fallback=vol.UNDEFINED):
            val = default_data.get(key)
            return val if val is not None else fallback

        schema = vol.Schema({
            vol.Required(CONF_SENSOR_GROUP_NAME, default=get_default(CONF_SENSOR_GROUP_NAME, "")): str,
            vol.Optional(CONF_WEATHER_ENTITY, default=get_default(CONF_WEATHER_ENTITY)): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="weather")
            ),
            vol.Required(CONF_REF_SENSOR, default=get_default(CONF_REF_SENSOR)): selector.EntitySelector(
                selector.EntitySelectorConfig(include_entities=valid_irradiance_sensors)
            ),
            vol.Required(CONF_REF_TILT, default=get_default(CONF_REF_TILT, 0)): vol.All(vol.Coerce(float), vol.Range(min=0, max=90)),
            vol.Required(CONF_REF_ORIENTATION, default=get_default(CONF_REF_ORIENTATION, 180)): vol.All(vol.Coerce(float), vol.Range(min=0, max=360)),
            vol.Required(CONF_TEMP_SENSOR, default=get_default(CONF_TEMP_SENSOR)): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
            ),
            vol.Optional(CONF_TEMP_PANEL_SENSOR, default=get_default(CONF_TEMP_PANEL_SENSOR)): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
            ),
            vol.Optional(CONF_WIND_SENSOR, default=get_default(CONF_WIND_SENSOR)): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="wind_speed")
            ),
        })
        return self.async_show_form(step_id=step_id, data_schema=schema, errors=errors)

    # =================================================================================
    # BRANCH 3: STRINGS (Integraciones - Create & Edit Only)
    # =================================================================================
    async def async_step_menu_strings(self, user_input=None):
        options = ["string_create_select_brand"]
        
        # Check if there are any strings created
        entries = self.hass.config_entries.async_entries(DOMAIN)
        string_count = sum(1 for e in entries if CONF_STRING_NAME in e.data)
        
        if string_count > 0:
            options.append("string_edit_select")

        return self.async_show_menu(
            step_id="menu_strings",
            menu_options=options 
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
            vol.Required(CONF_NUM_PANELS, default=1): vol.All(int, vol.Range(min=1)),
            vol.Required(CONF_NUM_STRINGS, default=1): vol.All(int, vol.Range(min=1)),
            vol.Required(CONF_TILT, default=30): vol.All(vol.Coerce(float), vol.Range(min=0, max=90)),
            vol.Required(CONF_AZIMUTH, default=180): vol.All(vol.Coerce(float), vol.Range(min=0, max=360)),
            vol.Optional(CONF_INVERTER_DEVICE): selector.DeviceSelector(
                selector.DeviceSelectorConfig()
            ),
        })
        return self.async_show_form(step_id="string_create_details", data_schema=schema)

    # 3.2 EDIT STRING - Select String
    async def async_step_string_edit_select(self, user_input=None):
        if user_input is not None:
             self.selected_item_id = user_input["selected_string"]
             # We need to load existing data to pre-fill
             # But ConfigEntries data is stored in HA, not our DB
             # We can find the entry by ID
             entry = self.hass.config_entries.async_get_entry(self.selected_item_id)
             if entry:
                 self.temp_data = entry.data.copy()
                 # We might jump directly to details if we assume Brand and Group don't change often?
                 # Or we can allow full edit. Let's allow full edit starting from Brand/Group.
                 # Pre-filling might be tricky if we want to change brand.
                 return await self.async_step_string_edit_details()
        
        # List ONLY our integration's entries
        entries = self.hass.config_entries.async_entries(DOMAIN)
        # Filter only "String" entries (those that have string_name or similar distinctive data)
        # Or better yet, we can filter by checking if they are NOT Sensor Groups?
        # A simpler way: Sensor Groups have 'sensor_group_name', Strings have 'string_name'
        string_options = {e.entry_id: e.title for e in entries if CONF_STRING_NAME in e.data}
        
        if not string_options:
             return self.async_abort(reason="no_strings_available")

        schema = vol.Schema({
            vol.Required("selected_string"): selector.SelectSelector(
                selector.SelectSelectorConfig(options=list(string_options.values()), custom_value=False, mode="dropdown")
                # Note: keys are IDs, but selector returns value? No, with options list it returns value if not set specific
                # Let's use Label/Value dict if possible or just list of IDs map to names?
                # Selector with simple list options returns the string selected.
            )
        })
        # Wait, SelectSelector with simple list returns the string. We need ID.
        # We need a map. {id: name}. SelectSelector options is list of strings or dicts {value: ..., label: ...}
        options_list = [{"value": k, "label": v} for k, v in string_options.items()]

        schema = vol.Schema({
            vol.Required("selected_string"): selector.SelectSelector(
                selector.SelectSelectorConfig(options=options_list, mode="dropdown")
            )
        })
        return self.async_show_form(step_id="string_edit_select", data_schema=schema)

    async def async_step_string_edit_details(self, user_input=None):
         # This needs to be similar to create but updating.
         # For simplicity in V1 for edit:
         # We just show the details form directly assuming user wants to tweak geometry/model.
         # If they want to change Brand/Group they might strictly need to recreate or we add 'step 1 edit'
         # Let's simple Edit Details only for now.
         
         if user_input is not None:
             # Update Entry
             entry = self.hass.config_entries.async_get_entry(self.selected_item_id)
             if entry:
                 new_data = {**entry.data, **user_input}
                 self.hass.config_entries.async_update_entry(entry, data=new_data)
                 return self.async_create_entry(title=f"Updated: {entry.title}", data={})
         
         # Load defaults
         default_data = self.temp_data
         
         # Note: We need the list of models for the *current* brand saved in data
         brand = default_data.get(CONF_BRAND, "Generic")
         models_filtered = self._db.list_models_by_brand(brand)
         
         schema = vol.Schema({
            vol.Required(CONF_PANEL_MODEL, default=default_data.get(CONF_PANEL_MODEL)): selector.SelectSelector(
                selector.SelectSelectorConfig(options=list(models_filtered.values()), mode="dropdown")
            ),
            vol.Required(CONF_NUM_PANELS, default=default_data.get(CONF_NUM_PANELS, 1)): vol.All(int, vol.Range(min=1)),
            vol.Required(CONF_NUM_STRINGS, default=default_data.get(CONF_NUM_STRINGS, 1)): vol.All(int, vol.Range(min=1)),
            vol.Required(CONF_TILT, default=default_data.get(CONF_TILT, 30)): vol.All(vol.Coerce(float), vol.Range(min=0, max=90)),
            vol.Required(CONF_AZIMUTH, default=default_data.get(CONF_AZIMUTH, 180)): vol.All(vol.Coerce(float), vol.Range(min=0, max=360)),
            vol.Optional(CONF_INVERTER_DEVICE, default=default_data.get(CONF_INVERTER_DEVICE)): selector.DeviceSelector(
                selector.DeviceSelectorConfig()
            ),
        })
         return self.async_show_form(step_id="string_edit_details", data_schema=schema)

    # =================================================================================
    # RECONFIGURE FLOW (Native "Configure" button support)
    # =================================================================================
    async def async_step_reconfigure(self, user_input=None):
        """Handle reconfiguration of an existing entry."""
        # Ensure DB is loaded (as async_step_user is not called here)
        self.hass.data.setdefault(DOMAIN, {})
        if "db" not in self.hass.data[DOMAIN]:
            self._db = PVDatabase(self.hass)
            await self._db.async_load()
            self.hass.data[DOMAIN]["db"] = self._db
        else:
            self._db = self.hass.data[DOMAIN]["db"]
            
        self.reconfigure_entry = self._get_reconfigure_entry()
        
        if CONF_SENSOR_GROUP_NAME in self.reconfigure_entry.data:
            return await self.async_step_reconfigure_sensor_group()
        elif CONF_STRING_NAME in self.reconfigure_entry.data:
            return await self.async_step_reconfigure_string()
            
        return self.async_abort(reason="unknown_entry_type")

    async def async_step_reconfigure_sensor_group(self, user_input=None):
        """Handle reconfiguration of a Sensor Group."""
        if user_input is not None:
             old_name = self.reconfigure_entry.data[CONF_SENSOR_GROUP_NAME]
             new_name = user_input[CONF_SENSOR_GROUP_NAME]
             
             # Update DB
             # If name changed, delete old DB entry (derived from old name)
             if old_name != new_name:
                 old_id = old_name.lower().replace(" ", "_")
                 # We try to delete, but simple delete_sensor_group might suffice
                 await self._db.delete_sensor_group(old_id)
                 
             await self._db.add_sensor_group(
                new_name,
                user_input[CONF_REF_SENSOR],
                user_input[CONF_TEMP_SENSOR],
                user_input.get(CONF_TEMP_PANEL_SENSOR),
                user_input.get(CONF_WIND_SENSOR),
                user_input[CONF_REF_TILT],
                user_input[CONF_REF_ORIENTATION],
                user_input.get(CONF_WEATHER_ENTITY)
             )
             
             # Update Config Entry
             self.hass.config_entries.async_update_entry(
                 self.reconfigure_entry, 
                 data=user_input, 
                 title=new_name
             )
             return self.async_update_reload_and_abort(self.reconfigure_entry)
             
        return self._show_sensor_group_form("reconfigure_sensor_group", {}, default_data=self.reconfigure_entry.data)

    async def async_step_reconfigure_string(self, user_input=None):
        """Handle reconfiguration of a String."""
        if user_input is not None:
             final_data = {**self.reconfigure_entry.data, **user_input}
             # For strings, if Brand changed, we are just updating data map. 
             # Logic is simpler as Strings don't have a separate DB entry, they rely on 'data'
             
             # Note: If String Name is in data, update title?
             # User input for 'string_edit_details' does NOT include string name or brand/group selection
             # If we want to allow editing those, we need a 2-step reconfigure or a fuller form.
             # Based on current 'edit' logic, we just show details.
             
             self.hass.config_entries.async_update_entry(
                 self.reconfigure_entry, 
                 data=final_data
             )
             return self.async_update_reload_and_abort(self.reconfigure_entry)
        
        # Determine defaults
        default_data = self.reconfigure_entry.data
        brand = default_data.get(CONF_BRAND, "Generic")
        models_filtered = self._db.list_models_by_brand(brand)
        
        # Reuse the schema from 'string_edit_details' logic
        # We can't reuse _show_form easily because 'string_edit_details' builds schema inline
        # So we duplicate the schema building here for safety and clarity
        schema = vol.Schema({
            vol.Required(CONF_PANEL_MODEL, default=default_data.get(CONF_PANEL_MODEL)): selector.SelectSelector(
                selector.SelectSelectorConfig(options=list(models_filtered.values()), mode="dropdown")
            ),
            vol.Required(CONF_NUM_PANELS, default=default_data.get(CONF_NUM_PANELS, 1)): vol.All(int, vol.Range(min=1)),
            vol.Required(CONF_NUM_STRINGS, default=default_data.get(CONF_NUM_STRINGS, 1)): vol.All(int, vol.Range(min=1)),
            vol.Required(CONF_TILT, default=default_data.get(CONF_TILT, 30)): vol.All(vol.Coerce(float), vol.Range(min=0, max=90)),
            vol.Required(CONF_AZIMUTH, default=default_data.get(CONF_AZIMUTH, 180)): vol.All(vol.Coerce(float), vol.Range(min=0, max=360)),
            vol.Optional(CONF_INVERTER_DEVICE, default=default_data.get(CONF_INVERTER_DEVICE)): selector.DeviceSelector(
                selector.DeviceSelectorConfig()
            ),
        })
        
        return self.async_show_form(step_id="reconfigure_string", data_schema=schema)