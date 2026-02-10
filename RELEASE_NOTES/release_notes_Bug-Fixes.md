# 🐛 Release Notes: Bug-Fixes (Hotfix)

**This release addresses a critical bug preventing the integration from starting.**

#### 🚑 Critical Fixes

* **Config Flow Startup:** Fixed an indentation error in `config_flow.py` that caused a syntax error, preventing the integration setup from completing successfully.

#### 🖌️ Changes from v1.1.0-beta2 (Included)

* **Bulk Creation Loop:** Added "Add another module" option after saving a PV Model to allow continuous creation without restarting the flow.
* **Improved Form Layouts:** Reordered Sensor Group fields for better UX (Tilt/Orientation moved up).
* **Consistent Menus:** All sub-menus (PV Models, Strings, Sensor Groups) now share a consistent title "Actions" // "Acciones".
* **Empty Forms:** PV Model creation forms now start empty (`vol.UNDEFINED`) instead of showing confusing default values.
* **Label Cleanups:** Removed redundant double asterisks (`**`) from required form fields.
* **Translations:** Synced ES/EN translations for new menu structures.

#### ⚠️ Upgrade Notes

* Please update to this version immediately if you experienced issues loading the integration with v1.1.0-beta2.

#### 🧪 Testing Instructions

1. Update to **Bug-Fixes** tag in HACS.
2. Restart Home Assistant.
3. Add the integration normally; it should now load the configuration menu without errors.
