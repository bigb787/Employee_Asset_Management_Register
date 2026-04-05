"""Column definitions and SQLite table names for Employee_Assets sub-tables (Laptop / Desktop / Monitor)."""
from __future__ import annotations

# (sql_column, display label) — order = table column order & UI order
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

KIND_SPECS: dict[str, dict] = {
    "laptops": {
        "table": "ea_laptops",
        "columns": LAPTOP_COLUMNS,
    },
    "desktops": {
        "table": "ea_desktops",
        "columns": DESKTOP_COLUMNS,
    },
    "monitors": {
        "table": "ea_monitors",
        "columns": MONITOR_COLUMNS,
    },
}


def fields_for_kind(kind: str) -> list[str]:
    return [c[0] for c in KIND_SPECS[kind]["columns"]]


def meta_payload() -> dict:
    out = {}
    for kind, spec in KIND_SPECS.items():
        out[kind] = {
            "columns": [{"key": k, "label": lab} for k, lab in spec["columns"]],
        }
    return out
