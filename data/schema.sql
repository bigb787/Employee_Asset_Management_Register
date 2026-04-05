-- Asset register — category chips (see eamr/dashboard_json.py CATEGORIES_META)
CREATE TABLE IF NOT EXISTS assets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  category TEXT NOT NULL CHECK (category IN (
    'employee_assets',
    'internal_assets',
    'external_assets',
    'cloud_assets',
    'admin_assets',
    'gatepass',
    'infodesk_leavers'
  )),
  serial_number TEXT,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_assets_category ON assets (category);

-- Employee_Assets: Laptop / Desktop / Monitor detail tables
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
