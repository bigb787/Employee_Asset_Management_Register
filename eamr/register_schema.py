"""Detail register: one chip = one table; column defs and panel layout for the dashboard."""
from __future__ import annotations

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

SCANNER_AND_OTHERS_COLUMNS: list[tuple[str, str]] = [
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

ADMIN_COLUMNS: list[tuple[str, str]] = [
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

# kind id == chip category_id for each row (API path /api/register-tables/{kind})
KIND_SPECS: dict[str, dict] = {
    "laptop": {"table": "ea_laptops", "columns": LAPTOP_COLUMNS},
    "desktop": {"table": "ea_desktops", "columns": DESKTOP_COLUMNS},
    "monitor": {"table": "ea_monitors", "columns": MONITOR_COLUMNS},
    "networking": {"table": "reg_networking", "columns": NETWORKING_COLUMNS},
    "cloud_asset_register": {"table": "reg_cloud_register", "columns": CLOUD_REGISTER_COLUMNS},
    "infodesk_applications": {"table": "reg_infodesk_apps", "columns": INFODESK_APPS_COLUMNS},
    "third_party_softwares": {"table": "reg_third_party_software", "columns": THIRD_PARTY_COLUMNS},
    "ups": {"table": "reg_admin_ups", "columns": ADMIN_UPS_COLUMNS},
    "mobile_phones": {"table": "reg_admin_mobile_phone", "columns": ADMIN_MOBILE_COLUMNS},
    "scanner_and_others": {"table": "reg_admin_scanners", "columns": SCANNER_AND_OTHERS_COLUMNS},
    "admin": {"table": "reg_admin", "columns": ADMIN_COLUMNS},
}


def _panel(category_id: str, title: str) -> dict:
    return {
        "category_id": category_id,
        "title": title,
        "tabs": [{"kind": category_id, "label": title}],
    }


# One top-level chip each; opening the chip shows this table (no sub-headers).
REGISTER_PANELS: list[dict] = [
    _panel("laptop", "Laptop"),
    _panel("desktop", "Desktop"),
    _panel("monitor", "Monitors"),
    _panel("networking", "Networking"),
    _panel("cloud_asset_register", "Cloud Asset Register"),
    _panel("infodesk_applications", "Infodesk Applications"),
    _panel("third_party_softwares", "Third Party Softwares"),
    _panel("ups", "UPS"),
    _panel("mobile_phones", "Mobile Phones"),
    _panel("scanner_and_others", "Scanner and Others"),
    _panel("admin", "Admin"),
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
