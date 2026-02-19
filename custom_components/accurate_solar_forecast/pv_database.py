import json
import os
from homeassistant.helpers.storage import Store
from .const import CONF_SENSOR_GROUP_NAME, CONF_REF_SENSOR, CONF_REF_TILT, CONF_REF_ORIENTATION, CONF_TEMP_SENSOR, CONF_WIND_SENSOR, CONF_TEMP_PANEL_SENSOR, CONF_WEATHER_ENTITY

STORAGE_VERSION = 1
STORAGE_KEY = "accurate_forecast_pv_models"

class PVDatabase:
    def __init__(self, hass):
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.data = {}
        self.sensor_groups = {} # Separate dictionary for sensor groups
        self.roofs = {}         # Separate dictionary for roofs

    async def async_load(self):
        """Carga la DB del disco."""
        data = await self._store.async_load()
        if data is None:
            # Datos por defecto si está vacío
            self.data = {
                "default_450w": {
                    "name": "Generico 450W",
                    "brand": "Generic",
                    "p_stc": 450,
                    "gamma": -0.35,
                    "noct": 45,
                    "voc": 49.0,
                    "isc": 11.5,
                    "vmp": 41.5,
                    "imp": 10.85
                }
            }
            self.sensor_groups = {}
            self.roofs = {}
            await self.async_save()
        else:
            # Handle migration or structure check if needed
            self.data = data.get("models", {})
            # If "models" key doesn't exist, assume old structure (root is models)
            if not self.data and data:
                 if "default_450w" in data or any("brand" in v for v in data.values()):
                     self.data = data
            
            self.sensor_groups = data.get("sensor_groups", {})
            self.roofs = data.get("roofs", {})

    async def async_save(self):
        """Guarda la DB al disco."""
        save_data = {
            "models": self.data,
            "sensor_groups": self.sensor_groups,
            "roofs": self.roofs
        }
        await self._store.async_save(save_data)

    # --- ROOF METHODS ---
    def add_roof(self, name):
        """Adds a roof to the database."""
        roof_id = name.lower().replace(" ", "_")
        if roof_id not in self.roofs:
            self.roofs[roof_id] = {
                "name": name
            }
            return self.async_save()
        return True # Already exists

    def list_roofs(self):
        """Returns a dict {id: name} of roofs."""
        return {k: v["name"] for k, v in self.roofs.items()}
    
    def get_roof(self, roof_id):
        return self.roofs.get(roof_id)

    # --- PV MODEL METHODS ---
    def add_model(self, name, brand, p_stc, gamma, noct, voc, isc, vmp, imp):
        model_id = name.lower().replace(" ", "_")
        self.data[model_id] = {
            "name": name,
            "brand": brand,
            "p_stc": p_stc,
            "gamma": gamma,
            "noct": noct,
            "voc": voc,
            "isc": isc,
            "vmp": vmp,
            "imp": imp
        }
        return self.async_save()

    async def delete_model(self, model_id):
        """Elimina un modelo de la DB."""
        if model_id == "default_450w":
            return False
            
        if model_id in self.data:
            del self.data[model_id]
            return await self.async_save()
        return False

    def get_model(self, model_id):
        return self.data.get(model_id)

    def list_brands(self):
        """Devuelve lista de marcas únicas."""
        brands = set()
        for v in self.data.values():
            brands.add(v.get("brand", "Generic"))
        if not brands:
            return ["Generic"]
        return sorted(list(brands))

    def list_models_by_brand(self, brand):
        """Devuelve dict {id: nombre} filtrado por marca."""
        return {
            k: v["name"] 
            for k, v in self.data.items() 
            if v.get("brand", "Generic") == brand
        }

    def list_models(self):
        """Devuelve dict {id: nombre} para el selector."""
        return {k: v["name"] for k, v in self.data.items()}

    # --- SENSOR GROUP METHODS ---
    def add_sensor_group(self, name, irradiance_sensor, temp_sensor, temp_panel_sensor, wind_sensor, ref_tilt, ref_orientation, weather_entity=None):
        group_id = name.lower().replace(" ", "_")
        self.sensor_groups[group_id] = {
            CONF_SENSOR_GROUP_NAME: name,
            CONF_REF_SENSOR: irradiance_sensor,
            CONF_TEMP_SENSOR: temp_sensor,
            CONF_TEMP_PANEL_SENSOR: temp_panel_sensor,
            CONF_WIND_SENSOR: wind_sensor,
            CONF_REF_TILT: ref_tilt,
            CONF_REF_ORIENTATION: ref_orientation,
            CONF_WEATHER_ENTITY: weather_entity
        }
        return self.async_save()
        
    def get_sensor_group(self, group_id):
        return self.sensor_groups.get(group_id)

    def list_sensor_groups(self):
        """Devuelve dict {id: nombre} para selectores."""
        if not self.sensor_groups or not isinstance(self.sensor_groups, dict):
            return {}
        return {
            k: v[CONF_SENSOR_GROUP_NAME] 
            for k, v in self.sensor_groups.items() 
            if isinstance(v, dict) and v.get(CONF_SENSOR_GROUP_NAME)
        }
    
    def delete_sensor_group(self, group_id):
        if group_id in self.sensor_groups:
            del self.sensor_groups[group_id]
            return self.async_save()
        return False