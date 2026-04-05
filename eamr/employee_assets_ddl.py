"""Standalone DDL for Employee_Assets tables (runs if missing from older DBs)."""
from __future__ import annotations

import sqlite3

EMPLOYEE_ASSETS_DDL = """
CREATE TABLE IF NOT EXISTS ea_laptops (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_type TEXT,
  asset_manufacturer TEXT,
  service_tag TEXT,
  model TEXT,
  pn TEXT,
  asset_owner TEXT,
  assigned_to TEXT,
  asset_status TEXT,
  last_owner TEXT,
  dept TEXT,
  location TEXT,
  asset_health TEXT,
  warranty TEXT,
  install_date TEXT,
  date_added_updated TEXT,
  processor TEXT,
  ram TEXT,
  harddisk TEXT,
  os TEXT,
  supt_vendor TEXT,
  keyboard TEXT,
  mouse TEXT,
  headphone TEXT,
  usb_extender TEXT,
  contains_pii TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS ea_desktops (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_type TEXT,
  asset_manufacturer TEXT,
  service_tag TEXT,
  model TEXT,
  pn TEXT,
  asset_owner TEXT,
  assigned_to TEXT,
  asset_status TEXT,
  last_owner TEXT,
  dept TEXT,
  location TEXT,
  asset_health TEXT,
  warranty TEXT,
  install_date TEXT,
  date_added_updated TEXT,
  processor TEXT,
  os TEXT,
  supt_vendor TEXT,
  configuration TEXT,
  contains_pii TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS ea_monitors (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_type TEXT,
  asset_manufacturer TEXT,
  service_tag TEXT,
  model TEXT,
  pn TEXT,
  asset_owner TEXT,
  assigned_to TEXT,
  asset_status TEXT,
  dept TEXT,
  location TEXT,
  asset_health TEXT,
  warranty TEXT,
  install_date TEXT,
  date_added_updated TEXT,
  supt_vendor TEXT,
  contains_pii TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);
"""


def ensure_employee_assets_tables(conn) -> None:
    """Create ea_* tables if this database was created before they existed."""
    try:
        conn.execute("SELECT 1 FROM ea_laptops LIMIT 1")
    except sqlite3.OperationalError:
        conn.executescript(EMPLOYEE_ASSETS_DDL)
