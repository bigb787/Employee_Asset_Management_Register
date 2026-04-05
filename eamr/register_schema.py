"""Detail register: column defs, SQLite table names, and panel/tab layout for dashboard chips."""
from __future__ import annotations

# --- Employee_Devices (Laptop / Desktop / Monitor / Accessories) ---

LAPTOP_COLUMNS: list[tuple[str, str]] = [
    ("asset_type", "Asset type"),
    ("asset_manufacturer", "Asset Manufacturer"),
    ("service_tag", "Service Tag"),
    ("model", "Model"),
    ("pn", "P/N"),
    ("asset_owner", "Asset Owner"),
    ("assigned_to", "Assigned To"),
    ("asset_status", "Asset Status"),
    ("last_owner", "Last Owner"),
    ("dept", "Dept"),
    ("location", "Location"),
    ("asset_health", "Asset Health"),
    ("warranty", "Warranty"),
    ("install_date", "Install date"),
    ("date_added_updated", "Date Added/Updated"),
    ("processor", "Processor"),
    ("ram", "RAM"),
    ("harddisk", "HardDisk"),
    ("os", "O/S"),
    ("supt_vendor", "Supt Vendor"),
    ("keyboard", "Keyboard"),
    ("mouse", "Mouse"),
    ("headphone", "HeadPhone"),
    ("usb_extender", "USB Extender"),
    ("contains_pii", "Contains PII (Yes/No)"),
]

DESKTOP_COLUMNS: list[tuple[str, str]] = [
    ("asset_type", "Asset type"),
    ("asset_manufacturer", "Asset Manufacturer"),
    ("service_tag", "Service Tag"),
    ("model", "Model"),
    ("pn", "P/N"),
    ("asset_owner", "Asset Owner"),
    ("assigned_to", "Assigned To"),
    ("asset_status", "Asset Status"),
    ("last_owner", "Last Owner"),
    ("dept", "Dept"),
    ("location", "Location"),
    ("asset_health", "Asset Health"),
    ("warranty", "Warranty"),
    ("install_date", "Install date"),
    ("date_added_updated", "Date Added/Updated"),
    ("processor", "Processor"),
    ("os", "O/S"),
    ("supt_vendor", "Supt Vendor"),
    ("configuration", "Configuration"),
    ("contains_pii", "Contains PII (Yes/No)"),
]

MONITOR_COLUMNS: list[tuple[str, str]] = [
    ("asset_type", "Asset type"),
    ("asset_manufacturer", "Asset Manufacturer"),
    ("service_tag", "Service Tag"),
    ("model", "Model"),
    ("pn", "P/N"),
    ("asset_owner", "Asset Owner"),
    ("assigned_to", "Assigned To"),
    ("asset_status", "Asset Status"),
    ("dept", "Dept"),
    ("location", "Location"),
    ("asset_health", "Asset Health"),
    ("warranty", "Warranty"),
    ("install_date", "INSTALL DATE"),
    ("date_added_updated", "Date Added/Updated"),
    ("supt_vendor", "Supt Vendor"),
    ("contains_pii", "Contains PII (Yes/No)"),
]

ACCESSORY_COLUMNS: list[tuple[str, str]] = [
    ("asset_type", "Asset type"),
    ("asset_manufacturer", "Asset Manufacturer"),
    ("service_tag", "Service Tag"),
    ("model", "Model"),
    ("pn", "P/N"),
    ("asset_owner", "Asset Owner"),
    ("assigned_to", "Assigned To"),
    ("dept", "Dept"),
    ("location", "Location"),
    ("warranty", "Warranty"),
    ("date_added_updated", "Date Added/Updated"),
    ("contains_pii", "Contains PII (Yes/No)"),
]

NETWORKING_COLUMNS: list[tuple[str, str]] = [
    ("asset_type", "Asset type"),
    ("asset_id", "Asset Id"),
    ("mac_id", "MAC ID"),
    ("asset_owner", "Asset Owner"),
    ("location", "Location"),
    ("model", "Model"),
    ("sn", "S/N"),
    ("pn", "P/N"),
    ("warranty", "Warranty"),
    ("install_date", "Install date"),
    ("os", "O/S"),
    ("supt_vendor", "Supt Vendor"),
    ("dept", "Dept"),
    ("configuration", "Configuration"),
    ("contains_pii", "Contains PII (Yes/No)"),
    ("date_added_updated", "Date Added/Updated"),
]

CLOUD_REGISTER_COLUMNS: list[tuple[str, str]] = [
    ("asset", "Asset"),
    ("asset_type", "Asset Type"),
    ("asset_value", "Asset Value"),
    ("asset_owner", "Asset Owner"),
    ("asset_location", "Asset Location"),
    ("contains_pii_data", "Contains PII data?"),
    ("asset_region", "Asset Region"),
    ("date_added_updated", "Date Added/ Updated"),
]

INFODESK_APPS_COLUMNS: list[tuple[str, str]] = [
    ("asset", "Asset"),
    ("asset_type", "Asset Type"),
    ("asset_value", "Asset Value"),
    ("asset_owner", "Asset Owner"),
    ("asset_location", "Asset Location"),
    ("contains_pii_data", "Contains PII data?"),
    ("date_added_updated", "Date Added/ Updated"),
]

THIRD_PARTY_COLUMNS: list[tuple[str, str]] = [
    ("asset", "Asset"),
    ("asset_type", "Asset Type"),
    ("asset_value", "Asset Value"),
    ("asset_owner", "Asset Owner"),
    ("asset_location", "Asset Location"),
    ("contains_pii_data", "Contains PII data?"),
    ("date_added_updated", "Date Added/ Updated"),
    ("cve_alert", "CVE alert"),
    ("setup", "Setup"),
    ("billing_api", "Billing API"),
]

ADMIN_UPS_COLUMNS: list[tuple[str, str]] = [
    ("asset_type", "Asset type"),
    ("device_id", "Device Id"),
    ("location", "Location"),
    ("model", "Model"),
    ("warranty", "Warranty"),
    ("install_date", "INSTALL DATE"),
    ("supt_vendor", "Supt Vendor"),
    ("dept", "Dept"),
    ("asset_owner", "Asset Owner"),
    ("contains_pii", "Contains PII (Yes/No)"),
    ("date_added_updated", "Date Added/Updated"),
]

ADMIN_MOBILE_COLUMNS: list[tuple[str, str]] = [
    ("asset_type", "Asset type"),
    ("device_id", "Device Id"),
    ("location", "Location"),
    ("model", "Model"),
    ("pn", "P/N"),
    ("warranty", "Warranty"),
    ("supt_vendor", "Supt Vendor"),
    ("dept", "Dept"),
    ("asset_owner", "Asset Owner"),
    ("contains_pii", "Contains PII (Yes/No)"),
    ("date_added_updated", "Date Added/Updated"),
]

ADMIN_SCANNERS_COLUMNS: list[tuple[str, str]] = [
    ("asset_type", "Asset type"),
    ("device_id", "Device Id"),
    ("location", "Location"),
    ("model", "Model"),
    ("service_tag", "Service Tag"),
    ("pn", "P/N"),
    ("warranty", "Warranty"),
    ("supt_vendor", "Supt Vendor"),
    ("dept", "Dept"),
    ("description", "Description"),
    ("asset_owner", "Asset Owner"),
    ("contains_pii", "Contains PII (Yes/No)"),
    ("date_added_updated", "Date Added/Updated"),
]

ADMIN_CAMERA_DVR_COLUMNS: list[tuple[str, str]] = [
    ("asset_type", "Asset type"),
    ("location", "Location"),
    ("invoice_no", "Invoice No"),
    ("warranty", "Warranty"),
    ("install_date", "INSTALL DATE"),
    ("supt_vendor", "Supt Vendor"),
    ("dept", "Dept"),
    ("asset_owner", "Asset Owner"),
    ("contains_pii", "Contains PII (Yes/No)"),
    ("date_added_updated", "Date Added/Updated"),
]

KIND_SPECS: dict[str, dict] = {
    "emp_laptop": {"table": "ea_laptops", "columns": LAPTOP_COLUMNS},
    "emp_desktop": {"table": "ea_desktops", "columns": DESKTOP_COLUMNS},
    "emp_monitor": {"table": "ea_monitors", "columns": MONITOR_COLUMNS},
    "emp_accessory": {"table": "reg_emp_accessory", "columns": ACCESSORY_COLUMNS},
    "networking": {"table": "reg_networking", "columns": NETWORKING_COLUMNS},
    "cloud_register": {"table": "reg_cloud_register", "columns": CLOUD_REGISTER_COLUMNS},
    "infodesk_apps": {"table": "reg_infodesk_apps", "columns": INFODESK_APPS_COLUMNS},
    "third_party_software": {"table": "reg_third_party_software", "columns": THIRD_PARTY_COLUMNS},
    "admin_ups": {"table": "reg_admin_ups", "columns": ADMIN_UPS_COLUMNS},
    "admin_mobile_phone": {"table": "reg_admin_mobile_phone", "columns": ADMIN_MOBILE_COLUMNS},
    "admin_scanners_printers": {"table": "reg_admin_scanners", "columns": ADMIN_SCANNERS_COLUMNS},
    "admin_camera": {"table": "reg_admin_camera", "columns": ADMIN_CAMERA_DVR_COLUMNS},
    "admin_dvr": {"table": "reg_admin_dvr", "columns": ADMIN_CAMERA_DVR_COLUMNS},
}

# Chip category id -> panel title + tabs (kind must exist in KIND_SPECS)
REGISTER_PANELS: list[dict] = [
    {
        "category_id": "employee_devices",
        "title": "Employee_Devices",
        "tabs": [
            {"kind": "emp_laptop", "label": "Laptop"},
            {"kind": "emp_desktop", "label": "Desktop"},
            {"kind": "emp_monitor", "label": "Monitors"},
            {"kind": "emp_accessory", "label": "Accessories"},
        ],
    },
    {
        "category_id": "networking",
        "title": "Networking",
        "tabs": [{"kind": "networking", "label": "Networking"}],
    },
    {
        "category_id": "cloud_asset_register",
        "title": "Cloud Asset Register",
        "tabs": [{"kind": "cloud_register", "label": "Cloud Asset Register"}],
    },
    {
        "category_id": "infodesk_applications",
        "title": "Infodesk Applications",
        "tabs": [{"kind": "infodesk_apps", "label": "Infodesk Applications"}],
    },
    {
        "category_id": "third_party_softwares",
        "title": "Third Party Softwares",
        "tabs": [{"kind": "third_party_software", "label": "Third Party Softwares"}],
    },
    {
        "category_id": "admin_devices",
        "title": "Admin Devices",
        "tabs": [
            {"kind": "admin_ups", "label": "UPS"},
            {"kind": "admin_mobile_phone", "label": "Mobile Phones"},
            {"kind": "admin_scanners_printers", "label": "Scanners and Printers"},
            {"kind": "admin_camera", "label": "Cameras"},
            {"kind": "admin_dvr", "label": "DVR"},
        ],
    },
]

DETAIL_CATEGORY_IDS = frozenset(p["category_id"] for p in REGISTER_PANELS)


def fields_for_kind(kind: str) -> list[str]:
    return [c[0] for c in KIND_SPECS[kind]["columns"]]


def meta_payload() -> dict:
    out: dict = {}
    for kind, spec in KIND_SPECS.items():
        out[kind] = {
            "columns": [{"key": k, "label": lab} for k, lab in spec["columns"]],
        }
    return out


def register_bootstrap_dict() -> dict:
    return {"kinds": meta_payload(), "panels": REGISTER_PANELS}
