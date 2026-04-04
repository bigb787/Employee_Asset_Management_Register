"""Server-side compliance summary (no UI)."""
from __future__ import annotations

from typing import Any, Optional

from app import database

ISO_CONTROLS = {
    "laptops": "A.8.1, A.5.9",
    "desktops": "A.8.1, A.5.9",
    "monitors": "A.8.1, A.5.9",
    "accessories": "A.8.1, A.5.9",
    "networking": "A.5.9, A.8.20",
    "cloud_assets": "A.5.9, A.5.23",
    "infodesk_applications": "A.5.9, A.8.26",
    "third_party_software": "A.5.19, A.8.7",
    "ups": "A.5.9",
    "mobile_phones": "A.8.1, A.5.9",
    "scanners_printers": "A.5.9",
    "cameras_dvr": "A.5.9",
    "gatepass": "A.5.11",
    "leavers_checklist": "A.6.5, A.5.11",
}

ASSET_TABLES = [
    "laptops",
    "desktops",
    "monitors",
    "accessories",
    "networking",
    "cloud_assets",
    "infodesk_applications",
    "third_party_software",
    "ups",
    "mobile_phones",
    "scanners_printers",
    "cameras_dvr",
]

COUNTRY_KEYS = ("India", "US", "UK", "Sweden")


def _norm(s: Optional[str]) -> str:
    return (s or "").strip()


def country_from_location(loc: Optional[str]) -> Optional[str]:
    t = _norm(loc)
    if not t:
        return None
    if "—" in t:
        c = t.split("—", 1)[0].strip()
    elif " - " in t:
        c = t.split(" - ", 1)[0].strip()
    else:
        c = t
    for k in COUNTRY_KEYS:
        if c.lower() == k.lower():
            return k
    return None


def _row_missing_owner(table: str, row: dict[str, Any]) -> bool:
    owner = row.get("asset_owner")
    if owner is not None and _norm(str(owner)):
        return False
    return True


def _row_missing_location(table: str, row: dict[str, Any]) -> bool:
    if table in ("cloud_assets", "infodesk_applications", "third_party_software"):
        loc = row.get("asset_location")
    else:
        loc = row.get("location")
    return not _norm(str(loc) if loc is not None else "")


def generate_iso_report(db: Any = None) -> dict[str, Any]:
    """Aggregate compliance metrics across asset tables. `db` unused; uses app.database."""
    _ = db
    total_assets: dict[str, int] = {}
    pii_count: dict[str, int] = {}
    confidential_count: dict[str, int] = {}
    missing_owner_count: dict[str, int] = {}
    missing_location_count: dict[str, int] = {}
    country_breakdown = {k: 0 for k in COUNTRY_KEYS}
    compliance_gaps: list[str] = []

    for table in ASSET_TABLES:
        try:
            rows = database.get_all(table)
        except Exception:
            rows = []
        total_assets[table] = len(rows)
        pii_count[table] = sum(
            1 for r in rows if _norm(str(r.get("contains_pii"))) == "Yes"
        )
        confidential_count[table] = sum(
            1
            for r in rows
            if _norm(str(r.get("iso_classification")))
            in ("Confidential", "Restricted")
        )
        m_owner = sum(1 for r in rows if _row_missing_owner(table, r))
        m_loc = sum(1 for r in rows if _row_missing_location(table, r))
        missing_owner_count[table] = m_owner
        missing_location_count[table] = m_loc
        for r in rows:
            loc = (
                r.get("asset_location")
                if table
                in ("cloud_assets", "infodesk_applications", "third_party_software")
                else r.get("location")
            )
            cty = country_from_location(str(loc) if loc is not None else None)
            if cty:
                country_breakdown[cty] += 1

        if m_owner:
            compliance_gaps.append(
                f"{table}: {m_owner} record(s) without asset owner (inventory gap)"
            )
        if m_loc:
            compliance_gaps.append(
                f"{table}: {m_loc} record(s) without location (inventory gap)"
            )
        high_pii = pii_count[table]
        if high_pii and confidential_count[table] < high_pii:
            compliance_gaps.append(
                f"{table}: review classification for {high_pii} PII-bearing asset(s)"
            )

    return {
        "total_assets": total_assets,
        "pii_count": pii_count,
        "confidential_count": confidential_count,
        "missing_owner_count": missing_owner_count,
        "missing_location_count": missing_location_count,
        "compliance_gaps": compliance_gaps,
        "country_breakdown": country_breakdown,
        "iso_controls": ISO_CONTROLS,
    }
