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
                    "p_stc": 450,
                    "gamma": -0.35,
                    "noct": 45
                }
            }
            await self.async_save()
        else:
            self.data = data

    async def async_save(self):
        """Guarda la DB al disco."""
        await self._store.async_save(self.data)

    def add_model(self, name, p_stc, gamma, noct):
        model_id = name.lower().replace(" ", "_")
        self.data[model_id] = {
            "name": name,
            "p_stc": p_stc,
            "gamma": gamma,
            "noct": noct
        }
        return self.async_save()

    def get_model(self, model_id):
        return self.data.get(model_id)

    def list_models(self):
        """Devuelve dict {id: nombre} para el selector."""
        return {k: v["name"] for k, v in self.data.items()}