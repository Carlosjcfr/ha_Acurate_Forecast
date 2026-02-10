# 🚀 Release Notes: v1.1.0-beta1 (Modular Config Flow)

**Changes in this pre-release focus on a complete overhaul of the configuration experience.**

#### ✨ New Features

* **Modular Management Menu:** The configuration flow has been completely redesigned. You can now manage all aspects of your solar setup from a single, organized menu:
  * **🏗️ Manage PV Models:** Create, Edit, or Delete panel specifications in your database.
  * **🌡️ Manage Sensor Groups:** Create and Edit your weather station configurations.
  * **☀️ Manage Strings:** Create new solar strings using your existing sensor groups and PV models.

* **CRUD for PV Models:** Full Create, Read, Update, and Delete functionality for your solar panel database directly from the UI. *No more stuck entries!*

* **Improved Deletion Handling:**
  * Deleting a **Sensor Group** or **String** integration from the Home Assistant Devices page now automatically cleans up the internal database, removing "ghost" entries from selection lists.

#### 🛠️ Technical Improvements

* **Refactored `config_flow.py`:** Migrated to a modular, branch-based architecture for better maintainability and scalability.
* **Unified Translations:** English and Spanish translations have been synchronized and updated to reflect the new menu structure, with clear indicators for required fields (*).

#### ⚠️ Breaking Changes

* The configuration flow steps have changed significantly.
* Existing configured devices should continue to work, but re-configuring them might show the new UI structure.

#### 🧪 Testing Instructions

1. HACS > Integrations > Accurate Solar Forecast > Redownload > **Show beta versions**.
2. Install **v1.1.0-beta1** and Restart Home Assistant.
3. Go to Settings > Devices > Add Integration > Accurate Solar Forecast.
4. Verify the new menu structure is present and working as expected.
5. Try creating a new PV Model, editing it, and then deleting it to test the full CRUD cycle.
6. Try deleting an existing Sensor Group integration from the HA Devices page and verify it no longer appears in the "Create String" dropdowns.

---

**Known Issues:**

* None reported yet. Please report any bugs found during testing!
