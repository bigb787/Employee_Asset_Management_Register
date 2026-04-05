-- Asset register — categories match dashboard chips
CREATE TABLE IF NOT EXISTS assets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  category TEXT NOT NULL CHECK (category IN (
    'employee_devices',
    'network',
    'cloud_assets',
    'infodesk_apps',
    'third_party'
  )),
  serial_number TEXT,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_assets_category ON assets (category);
