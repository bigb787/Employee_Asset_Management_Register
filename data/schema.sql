-- Asset register — four category headers: Employee_Assets, Internal / External / Admin Assets
CREATE TABLE IF NOT EXISTS assets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  category TEXT NOT NULL CHECK (category IN (
    'employee_assets',
    'internal_assets',
    'external_assets',
    'admin_assets'
  )),
  serial_number TEXT,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_assets_category ON assets (category);
