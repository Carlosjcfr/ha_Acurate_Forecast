import json
import os
from homeassistant.helpers.storage import Store

STORAGE_VERSION = 1
STORAGE_KEY = "accurate_forecast_pv_models"

class PVDatabase:
    def __init__(self, hass):
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.data = {}

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
            await self.async_save()
        else:
            self.data = data

    async def async_save(self):
        """Guarda la DB al disco."""
        await self._store.async_save(self.data)

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
        }
        return self.async_save()

    def delete_model(self, model_id):
        """Elimina un modelo de la DB."""
        if model_id in self.data:
            del self.data[model_id]
            return self.async_save()
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