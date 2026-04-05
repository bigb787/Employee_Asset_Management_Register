-- Asset register — category chips (see eamr/dashboard_json.py CATEGORIES_META)
CREATE TABLE IF NOT EXISTS assets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  category TEXT NOT NULL CHECK (category IN (
    'laptop',
    'desktop',
    'monitor',
    'networking',
    'cloud_asset_register',
    'infodesk_applications',
    'third_party_softwares',
    'ups',
    'mobile_phones',
    'scanner_and_others',
    'admin',
    'gatepass',
    'infodesk_leavers'
  )),
  serial_number TEXT,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_assets_category ON assets (category);

-- Laptop / Desktop / Monitor detail tables
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

CREATE TABLE IF NOT EXISTS reg_networking (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_type TEXT,
  asset_id TEXT,
  mac_id TEXT,
  asset_owner TEXT,
  location TEXT,
  model TEXT,
  sn TEXT,
  pn TEXT,
  warranty TEXT,
  install_date TEXT,
  os TEXT,
  supt_vendor TEXT,
  dept TEXT,
  configuration TEXT,
  contains_pii TEXT,
  date_added_updated TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS reg_cloud_register (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset TEXT,
  asset_type TEXT,
  asset_value TEXT,
  asset_owner TEXT,
  asset_location TEXT,
  contains_pii_data TEXT,
  asset_region TEXT,
  date_added_updated TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS reg_infodesk_apps (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset TEXT,
  asset_type TEXT,
  asset_value TEXT,
  asset_owner TEXT,
  asset_location TEXT,
  contains_pii_data TEXT,
  date_added_updated TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS reg_third_party_software (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset TEXT,
  asset_type TEXT,
  asset_value TEXT,
  asset_owner TEXT,
  asset_location TEXT,
  contains_pii_data TEXT,
  date_added_updated TEXT,
  cve_alert TEXT,
  setup TEXT,
  billing_api TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS reg_admin_ups (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_type TEXT,
  device_id TEXT,
  location TEXT,
  model TEXT,
  warranty TEXT,
  install_date TEXT,
  supt_vendor TEXT,
  dept TEXT,
  asset_owner TEXT,
  contains_pii TEXT,
  date_added_updated TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS reg_admin_mobile_phone (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_type TEXT,
  device_id TEXT,
  location TEXT,
  model TEXT,
  pn TEXT,
  warranty TEXT,
  supt_vendor TEXT,
  dept TEXT,
  asset_owner TEXT,
  contains_pii TEXT,
  date_added_updated TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS reg_admin_scanners (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_type TEXT,
  device_id TEXT,
  location TEXT,
  model TEXT,
  service_tag TEXT,
  pn TEXT,
  warranty TEXT,
  supt_vendor TEXT,
  dept TEXT,
  description TEXT,
  asset_owner TEXT,
  contains_pii TEXT,
  date_added_updated TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS reg_admin (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_type TEXT,
  location TEXT,
  invoice_no TEXT,
  warranty TEXT,
  install_date TEXT,
  supt_vendor TEXT,
  dept TEXT,
  asset_owner TEXT,
  contains_pii TEXT,
  date_added_updated TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);
