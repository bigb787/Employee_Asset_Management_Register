/* Employee Asset Register — vanilla JS UI */
(function () {
  'use strict';

  const LOCATIONS = {
    India: ['Vadodara', 'Ahmedabad', 'Mumbai', 'Bangalore', 'Delhi', 'Pune', 'Chennai', 'Hyderabad', 'Other India'],
    US: ['New York', 'San Francisco', 'Austin', 'Chicago', 'Los Angeles', 'Seattle', 'Other US'],
    UK: ['London', 'Manchester', 'Birmingham', 'Edinburgh', 'Bristol', 'Other UK'],
    Sweden: ['Stockholm', 'Gothenburg', 'Malmö', 'Uppsala', 'Other Sweden'],
  };

  const FLAGS = { India: '🇮🇳', US: '🇺🇸', UK: '🇬🇧', Sweden: '🇸🇪' };

  const OFFICE_OPTIONS = [];
  Object.keys(LOCATIONS).forEach((country) => {
    LOCATIONS[country].forEach((city) => {
      OFFICE_OPTIONS.push({ display: city, value: `${country} — ${city}` });
    });
  });

  const SYSTEM_KEYS = [
    'email_groups', 'infodesk_qa_dev', 'infodesk_prod', 'jira_and_wiki', 'ms_office', 'mongo_access',
    'azure_infodesk', 'azure_wn_infodesk', 'vpn', 'wn_vpn', 'azure_devops', 'info_admin', 'zabbix',
    'github', 'infodesk_portal', 'salesforce',
  ];

  const SYSTEM_LABELS = [
    ['Email Groups', 'email_groups'],
    ['Infodesk QA/Dev', 'infodesk_qa_dev'],
    ['Infodesk Prod', 'infodesk_prod'],
    ['JIRA and Wiki', 'jira_and_wiki'],
    ['MS Office', 'ms_office'],
    ['Mongo Access', 'mongo_access'],
    ['Azure Infodesk', 'azure_infodesk'],
    ['Azure WN InfoDesk', 'azure_wn_infodesk'],
    ['VPN', 'vpn'],
    ['WN VPN', 'wn_vpn'],
    ['Azure Devops', 'azure_devops'],
    ['InfoAdmin', 'info_admin'],
    ['Zabbix', 'zabbix'],
    ['GitHub', 'github'],
    ['InfoDesk Portal', 'infodesk_portal'],
    ['Salesforce', 'salesforce'],
  ];

  const state = {
    tab: 'employee',
    stats: {},
    rawEmployee: [],
    rawAdmin: [],
    rawNetworking: [],
    rawCloud: [],
    rawInfodesk: [],
    rawThirdParty: [],
    rawGatepass: [],
    rawLeavers: [],
    auditPage: 1,
    auditTotal: 0,
    auditItems: [],
    empChip: 'all',
    admChip: 'all',
    editing: null,
    gatepassItems: [],
    modalMode: null,
    leaverFile: null,
  };

  const $ = (sel, el = document) => el.querySelector(sel);
  const $$ = (sel, el = document) => Array.from(el.querySelectorAll(sel));

  function esc(s) {
    if (s == null || s === '') return '';
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function showToast(msg) {
    const t = $('#toast');
    t.textContent = msg;
    t.hidden = false;
    clearTimeout(showToast._tm);
    showToast._tm = setTimeout(() => { t.hidden = true; }, 3200);
  }

  async function api(path, opts = {}) {
    const r = await fetch(path, {
      headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
      ...opts,
    });
    if (!r.ok) {
      let detail = r.statusText;
      try {
        const j = await r.json();
        if (j.detail) detail = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
      } catch (_) { /* ignore */ }
      throw new Error(detail || 'Request failed');
    }
    if (r.status === 204) return null;
    const ct = r.headers.get('content-type') || '';
    if (ct.includes('application/json')) return r.json();
    return r.text();
  }

  function formatLocationDisplay(loc) {
    if (!loc) return '';
    const t = String(loc).trim();
    const parts = t.split(/[—\-]/).map((s) => s.trim()).filter(Boolean);
    if (parts.length >= 2) {
      const country = parts[0];
      const city = parts.slice(1).join(' — ');
      const f = FLAGS[country] || '';
      return f ? `${f} ${city}` : t;
    }
    return t;
  }

  function parseLocationValue(stored) {
    if (!stored) return { country: '', city: '', value: '' };
    const t = String(stored).trim();
    const idx = t.indexOf('—');
    if (idx === -1) return { country: '', city: t, value: t };
    return {
      country: t.slice(0, idx).trim(),
      city: t.slice(idx + 1).trim(),
      value: t,
    };
  }

  function officeSelectHtml(id, required) {
    const req = required ? ' required' : '';
    let opts = `<option value="">${required ? 'Select office…' : ''}</option>`;
    OFFICE_OPTIONS.forEach((o) => {
      opts += `<option value="${esc(o.value)}">${esc(o.display)}</option>`;
    });
    return `<select id="${id}" class="loc-office"${req}>${opts}</select>`;
  }

  function setOfficeSelectValue(selectId, storedLocation) {
    const sel = document.getElementById(selectId);
    if (!sel) return;
    const { value } = parseLocationValue(storedLocation);
    sel.value = value || '';
  }

  function badgeStatusAsset(v) {
    const x = String(v || '').trim();
    const m = {
      Active: 'badge-st-active',
      Idle: 'badge-st-idle',
      Maintenance: 'badge-st-maintenance',
      Faulty: 'badge-st-faulty',
    };
    const cls = m[x] || '';
    return `<span class="badge ${cls}">${esc(x || '—')}</span>`;
  }

  function badgeHealth(v) {
    const x = String(v || '').trim();
    const m = {
      Good: 'badge-h-good',
      Fair: 'badge-h-fair',
      Poor: 'badge-h-poor',
      'Under Repair': 'badge-h-repair',
    };
    const cls = m[x] || '';
    return `<span class="badge ${cls}">${esc(x || '—')}</span>`;
  }

  function badgePii(v) {
    const x = String(v || '').trim();
    const cls = x === 'Yes' ? 'badge-pii-yes' : x === 'No' ? 'badge-pii-no' : '';
    return `<span class="badge ${cls}">${esc(x || '—')}</span>`;
  }

  function badgeIso(v) {
    const x = String(v || '').trim();
    const m = {
      Public: 'badge-iso-public',
      Internal: 'badge-iso-internal',
      Confidential: 'badge-iso-confidential',
      Restricted: 'badge-iso-restricted',
    };
    const cls = m[x] || '';
    return `<span class="badge ${cls}">${esc(x || '—')}</span>`;
  }

  function badgeCve(v) {
    const x = String(v || '').trim();
    const m = {
      None: 'badge-cve-none',
      Low: 'badge-cve-low',
      Medium: 'badge-cve-medium',
      High: 'badge-cve-high',
      Critical: 'badge-cve-critical',
    };
    const cls = m[x] || '';
    return `<span class="badge ${cls}">${esc(x || '—')}</span>`;
  }

  function badgePatch(v) {
    return `<span class="badge badge-st-idle">${esc(String(v || '—'))}</span>`;
  }

  function badgeGatepassStatus(v) {
    const x = String(v || '').trim();
    const m = { Open: 'badge-gp-open', Closed: 'badge-gp-closed', Cancelled: 'badge-gp-cancel' };
    const cls = m[x] || '';
    return `<span class="badge ${cls}">${esc(x || '—')}</span>`;
  }

  function badgeOverall(v) {
    const x = String(v || '').trim();
    const m = {
      'In Progress': 'badge-ov-inprogress',
      Completed: 'badge-ov-completed',
      'On Hold': 'badge-ov-hold',
    };
    const cls = m[x] || '';
    return `<span class="badge ${cls}">${esc(x || '—')}</span>`;
  }

  function calcProgress(c) {
    const done = SYSTEM_KEYS.filter((s) => {
      const z = String(c[s] || '').trim();
      return z === 'Revoked' || z === 'N/A';
    }).length;
    const hw = String(c.hw_handed_over || '').trim() === 'Yes' ? 1 : 0;
    const ev = c.evidence_file_s3_key || c.evidence_file_url ? 1 : 0;
    const total = SYSTEM_KEYS.length + 2;
    const pct = total ? Math.round(((done + hw + ev) / total) * 100) : 0;
    return { done: done + hw + ev, total, pct };
  }

  function deriveOverallStatus(c) {
    const { pct } = calcProgress(c);
    const p = String(c.it_peer_review || '').trim();
    const r = String(c.reporting_manager || '').trim();
    const a = String(c.confirmation_audit || '').trim();
    if (String(c.it_peer_review || '').trim() === 'Rejected'
      || String(c.reporting_manager || '').trim() === 'Rejected'
      || String(c.confirmation_audit || '').trim() === 'Rejected') {
      return 'On Hold';
    }
    if (pct === 100 && p === 'Approved' && r === 'Approved' && a === 'Approved') return 'Completed';
    return 'In Progress';
  }

  function currentRawRows() {
    switch (state.tab) {
      case 'employee': return state.rawEmployee;
      case 'admin': return state.rawAdmin;
      case 'networking': return state.rawNetworking;
      case 'cloud': return state.rawCloud;
      case 'infodesk': return state.rawInfodesk;
      case 'third_party': return state.rawThirdParty;
      case 'gatepass': return state.rawGatepass;
      case 'leavers': return state.rawLeavers;
      default: return [];
    }
  }

  function filterByChipEmployee(rows) {
    const ch = state.empChip;
    if (ch === 'all') return rows;
    const map = {
      laptop: 'laptops',
      desktop: 'desktops',
      monitor: 'monitors',
      accessory: 'accessories',
    };
    const tbl = map[ch];
    return rows.filter((r) => r.__table === tbl);
  }

  function filterByChipAdmin(rows) {
    const ch = state.admChip;
    if (ch === 'all') return rows;
    return rows.filter((r) => {
      if (ch === 'ups') return r.__table === 'ups';
      if (ch === 'mobile') return r.__table === 'mobile_phones';
      if (ch === 'scanner') return r.__table === 'scanners_printers';
      if (ch === 'camera') return r.__table === 'cameras_dvr';
      return true;
    });
  }

  function rowMatchesSearch(row, q) {
    if (!q) return true;
    const ql = q.toLowerCase();
    return Object.values(row).some((v) => v != null && String(v).toLowerCase().includes(ql));
  }

  function statusColumnForRow(row) {
    if (row.__table === 'gatepass') return 'status';
    if (row.__table === 'leavers_checklist') return 'overall_status';
    if (['laptops', 'desktops', 'monitors', 'accessories'].includes(row.__table)) return 'asset_status';
    return null;
  }

  function deptKeyForRow(row) {
    const t = row.__table;
    if (t === 'leavers_checklist') return 'department';
    if (t === 'gatepass') return 'dept_head';
    if (['cloud_assets', 'infodesk_applications', 'third_party_software'].includes(t)) return null;
    return 'dept';
  }

  function locationKeyForRow(row) {
    const t = row.__table;
    if (t === 'leavers_checklist') return 'hw_inventory_location';
    if (['cloud_assets', 'infodesk_applications', 'third_party_software'].includes(t)) return 'asset_location';
    return 'location';
  }

  function piiKeyForRow(row) {
    const t = row.__table;
    if (['gatepass', 'leavers_checklist', 'audit_log'].includes(t)) return null;
    return 'contains_pii';
  }

  function isoKeyForRow(row) {
    const t = row.__table;
    if (['gatepass', 'leavers_checklist', 'audit_log'].includes(t)) return null;
    return 'iso_classification';
  }

  function applyFilters(rows, skipLocation, skipDept) {
    const q = ($('#f-search').value || '').trim();
    const st = $('#f-status').value;
    const dept = $('#f-dept').value;
    const loc = $('#f-location').value;
    const pii = $('#f-pii').value;
    const iso = $('#f-iso').value;

    let out = rows.slice();
    if (state.tab === 'employee') out = filterByChipEmployee(out);
    if (state.tab === 'admin') out = filterByChipAdmin(out);

    out = out.filter((r) => rowMatchesSearch(r, q));

    if (st && st !== 'All') {
      out = out.filter((r) => {
        const col = statusColumnForRow(r);
        if (!col) return true;
        return String(r[col] || '').trim() === st;
      });
    }

    if (!skipDept && dept && dept !== 'All') {
      out = out.filter((r) => {
        const col = deptKeyForRow(r);
        if (!col) return true;
        return String(r[col] || '').trim() === dept;
      });
    }

    if (!skipLocation && loc && loc !== 'All') {
      out = out.filter((r) => {
        const col = locationKeyForRow(r);
        if (!col) return true;
        return String(r[col] || '').includes(loc);
      });
    }

    if (pii && pii !== 'All') {
      out = out.filter((r) => {
        const col = piiKeyForRow(r);
        if (!col) return true;
        return String(r[col] || '').trim() === pii;
      });
    }

    if (iso && iso !== 'All') {
      out = out.filter((r) => {
        const col = isoKeyForRow(r);
        if (!col) return true;
        return String(r[col] || '').trim() === iso;
      });
    }

    return out;
  }

  function uniqueDepts(rows) {
    const set = new Set();
    rows.forEach((r) => {
      const col = deptKeyForRow(r);
      if (!col) return;
      const v = String(r[col] || '').trim();
      if (v) set.add(v);
    });
    return Array.from(set).sort();
  }

  function locationCounts(rows) {
    const counts = {};
    Object.keys(LOCATIONS).forEach((c) => {
      LOCATIONS[c].forEach((city) => {
        counts[city] = (counts[city] || 0);
      });
    });
    rows.forEach((r) => {
      const col = locationKeyForRow(r);
      if (!col) return;
      const raw = String(r[col] || '').trim();
      if (!raw) return;
      const city = parseLocationValue(raw).city || raw;
      counts[city] = (counts[city] || 0) + 1;
    });
    return counts;
  }

  function rebuildDeptFilter() {
    const sel = $('#f-dept');
    const cur = sel.value;
    const rows = applyFilters(currentRawRows(), true, true);
    const depts = uniqueDepts(rows);
    sel.innerHTML = '<option value="All">All departments</option>';
    depts.forEach((d) => {
      sel.innerHTML += `<option>${esc(d)}</option>`;
    });
    if ([...sel.options].some((o) => o.value === cur)) sel.value = cur;
  }

  function rebuildLocationFilter() {
    const sel = $('#f-location');
    const cur = sel.value;
    const rows = applyFilters(currentRawRows(), true, false);
    const cnt = locationCounts(rows);
    let html = '<option value="All">All locations</option>';
    Object.keys(LOCATIONS).forEach((country) => {
      html += `<optgroup label="── ${country} ─────────────">`;
      LOCATIONS[country].forEach((city) => {
        const n = cnt[city] || 0;
        html += `<option value="${esc(city)}">${esc(city)} (${n})</option>`;
      });
      html += '</optgroup>';
    });
    sel.innerHTML = html;
    if ([...sel.options].some((o) => o.value === cur)) sel.value = cur;
  }

  function renderActiveFilterChips() {
    const host = $('#active-filters');
    host.innerHTML = '';
    const parts = [];
    const q = ($('#f-search').value || '').trim();
    if (q) parts.push({ key: 'search', label: `Search: ${q}` });
    if ($('#f-status').value && $('#f-status').value !== 'All') parts.push({ key: 'status', label: `Status: ${$('#f-status').value}` });
    if ($('#f-dept').value && $('#f-dept').value !== 'All') parts.push({ key: 'dept', label: `Dept: ${$('#f-dept').value}` });
    if ($('#f-location').value && $('#f-location').value !== 'All') {
      const city = $('#f-location').value;
      const country = Object.keys(LOCATIONS).find((c) => LOCATIONS[c].includes(city)) || '';
      const flag = FLAGS[country] || '';
      parts.push({ key: 'location', label: `Location: ${flag} ${city}`.trim() });
    }
    if ($('#f-pii').value && $('#f-pii').value !== 'All') parts.push({ key: 'pii', label: `PII: ${$('#f-pii').value}` });
    if ($('#f-iso').value && $('#f-iso').value !== 'All') parts.push({ key: 'iso', label: `Class: ${$('#f-iso').value}` });

    parts.forEach((p) => {
      const el = document.createElement('span');
      el.className = 'filter-chip';
      el.innerHTML = `${esc(p.label)} <button type="button" data-clear="${esc(p.key)}" aria-label="Clear">×</button>`;
      host.appendChild(el);
    });

    host.querySelectorAll('button[data-clear]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const k = btn.getAttribute('data-clear');
        if (k === 'search') $('#f-search').value = '';
        if (k === 'status') $('#f-status').value = 'All';
        if (k === 'dept') $('#f-dept').value = 'All';
        if (k === 'location') $('#f-location').value = 'All';
        if (k === 'pii') $('#f-pii').value = 'All';
        if (k === 'iso') $('#f-iso').value = 'All';
        rebuildDeptFilter();
        rebuildLocationFilter();
        renderTable();
      });
    });
  }

  function locationResultBar(filteredRows) {
    const bar = $('#result-bar');
    const loc = $('#f-location').value;
    if (!loc || loc === 'All') {
      bar.hidden = true;
      return;
    }
    const country = Object.keys(LOCATIONS).find((c) => LOCATIONS[c].includes(loc)) || '';
    const flag = FLAGS[country] || '';
    const n = filteredRows.length;

    const typeCounts = {};
    filteredRows.forEach((r) => {
      const t = String(r.asset_type || r.__table || '').trim() || 'Record';
      typeCounts[t] = (typeCounts[t] || 0) + 1;
    });
    const breakdown = Object.entries(typeCounts)
      .map(([k, v]) => `${v} ${k}`)
      .join(' · ');

    bar.innerHTML = `<strong>${n}</strong> assets found — ${flag} ${esc(loc)}<br/><span class="muted">${esc(breakdown)}</span>`;
    bar.hidden = false;
  }

  function actionsCell(html) {
    return `<td class="cell-actions">${html}</td>`;
  }

  function empActions(r, table) {
    return `<button type="button" class="link" data-act="edit" data-table="${table}" data-id="${r.id}">Edit</button>
      <button type="button" class="link" data-act="del" data-table="${table}" data-id="${r.id}">Delete</button>`;
  }

  function catLabel(t) {
    const m = {
      laptops: 'Laptop',
      desktops: 'Desktop',
      monitors: 'Monitor',
      accessories: 'Accessory',
      ups: 'UPS',
      mobile_phones: 'Mobile Phone',
      scanners_printers: 'Scanner/Printer',
      cameras_dvr: 'Camera/DVR',
    };
    return m[t] || t;
  }

  function tagCell(r) {
    return esc(r.service_tag || r.device_id || r.model || '—');
  }

  function renderEmployeeTable(rows) {
    const thead = $('#data-thead');
    const tbody = $('#data-tbody');
    const ch = state.empChip;

    if (ch === 'all') {
      thead.innerHTML = `<tr>
        <th>Category</th><th>Asset Type</th><th>Manufacturer</th><th>Tag / ID</th><th>Model</th>
        <th>Asset Owner</th><th>Assigned To</th><th>Asset Status</th><th>Dept</th><th>Location</th>
        <th>Contains PII</th><th>ISO Class</th><th>Actions</th></tr>`;
      tbody.innerHTML = rows.map((r) => `<tr>
        <td>${esc(catLabel(r.__table))}</td><td>${esc(r.asset_type)}</td><td>${esc(r.asset_manufacturer)}</td>
        <td>${tagCell(r)}</td><td>${esc(r.model)}</td>
        <td>${esc(r.asset_owner)}</td><td>${esc(r.assigned_to)}</td><td>${badgeStatusAsset(r.asset_status)}</td>
        <td>${esc(r.dept)}</td><td>${formatLocationDisplay(r.location)}</td>
        <td>${badgePii(r.contains_pii)}</td><td>${badgeIso(r.iso_classification)}</td>
        ${actionsCell(empActions(r, r.__table))}</tr>`).join('');
      return;
    }

    if (ch === 'laptop') {
      thead.innerHTML = `<tr>
        <th>Asset Type</th><th>Manufacturer</th><th>Service Tag</th><th>Model</th><th>P/N</th>
        <th>Asset Owner</th><th>Assigned To</th><th>Asset Status</th><th>Last Owner</th>
        <th>Dept</th><th>Location</th><th>Asset Health</th><th>Warranty</th><th>Install Date</th>
        <th>Date Added/Updated</th><th>Processor</th><th>RAM</th><th>Hard Disk</th><th>O/S</th>
        <th>Supt Vendor</th><th>Keyboard</th><th>Mouse</th><th>Headphone</th><th>USB Extender</th>
        <th>Contains PII</th><th>ISO Class</th><th>Actions</th></tr>`;
      tbody.innerHTML = rows.map((r) => `<tr>
        <td>${esc(r.asset_type)}</td><td>${esc(r.asset_manufacturer)}</td><td>${esc(r.service_tag)}</td><td>${esc(r.model)}</td><td>${esc(r.pn)}</td>
        <td>${esc(r.asset_owner)}</td><td>${esc(r.assigned_to)}</td><td>${badgeStatusAsset(r.asset_status)}</td><td>${esc(r.last_owner)}</td>
        <td>${esc(r.dept)}</td><td>${formatLocationDisplay(r.location)}</td><td>${badgeHealth(r.asset_health)}</td>
        <td>${esc(r.warranty)}</td><td>${esc(r.install_date)}</td><td>${esc(r.date_added_updated)}</td>
        <td>${esc(r.processor)}</td><td>${esc(r.ram)}</td><td>${esc(r.hard_disk)}</td><td>${esc(r.os)}</td>
        <td>${esc(r.supt_vendor)}</td><td>${esc(r.keyboard)}</td><td>${esc(r.mouse)}</td><td>${esc(r.headphone)}</td><td>${esc(r.usb_extender)}</td>
        <td>${badgePii(r.contains_pii)}</td><td>${badgeIso(r.iso_classification)}</td>
        ${actionsCell(empActions(r, 'laptops'))}</tr>`).join('');
      return;
    }

    if (ch === 'desktop') {
      thead.innerHTML = `<tr>
        <th>Asset Type</th><th>Manufacturer</th><th>Service Tag</th><th>Model</th><th>P/N</th>
        <th>Asset Owner</th><th>Assigned To</th><th>Asset Status</th><th>Last Owner</th>
        <th>Dept</th><th>Location</th><th>Asset Health</th><th>Warranty</th><th>Install Date</th>
        <th>Date Added/Updated</th><th>Processor</th><th>O/S</th><th>Supt Vendor</th><th>Configuration</th>
        <th>Contains PII</th><th>ISO Class</th><th>Actions</th></tr>`;
      tbody.innerHTML = rows.map((r) => `<tr>
        <td>${esc(r.asset_type)}</td><td>${esc(r.asset_manufacturer)}</td><td>${esc(r.service_tag)}</td><td>${esc(r.model)}</td><td>${esc(r.pn)}</td>
        <td>${esc(r.asset_owner)}</td><td>${esc(r.assigned_to)}</td><td>${badgeStatusAsset(r.asset_status)}</td><td>${esc(r.last_owner)}</td>
        <td>${esc(r.dept)}</td><td>${formatLocationDisplay(r.location)}</td><td>${badgeHealth(r.asset_health)}</td>
        <td>${esc(r.warranty)}</td><td>${esc(r.install_date)}</td><td>${esc(r.date_added_updated)}</td>
        <td>${esc(r.processor)}</td><td>${esc(r.os)}</td><td>${esc(r.supt_vendor)}</td><td>${esc(r.configuration)}</td>
        <td>${badgePii(r.contains_pii)}</td><td>${badgeIso(r.iso_classification)}</td>
        ${actionsCell(empActions(r, 'desktops'))}</tr>`).join('');
      return;
    }

    if (ch === 'monitor') {
      thead.innerHTML = `<tr>
        <th>Asset Type</th><th>Manufacturer</th><th>Service Tag</th><th>Model</th><th>P/N</th>
        <th>Asset Owner</th><th>Assigned To</th><th>Asset Status</th><th>Dept</th><th>Location</th>
        <th>Asset Health</th><th>Warranty</th><th>Install Date</th><th>Date Added/Updated</th>
        <th>Supt Vendor</th><th>Contains PII</th><th>ISO Class</th><th>Actions</th></tr>`;
      tbody.innerHTML = rows.map((r) => `<tr>
        <td>${esc(r.asset_type)}</td><td>${esc(r.asset_manufacturer)}</td><td>${esc(r.service_tag)}</td><td>${esc(r.model)}</td><td>${esc(r.pn)}</td>
        <td>${esc(r.asset_owner)}</td><td>${esc(r.assigned_to)}</td><td>${badgeStatusAsset(r.asset_status)}</td>
        <td>${esc(r.dept)}</td><td>${formatLocationDisplay(r.location)}</td><td>${badgeHealth(r.asset_health)}</td>
        <td>${esc(r.warranty)}</td><td>${esc(r.install_date)}</td><td>${esc(r.date_added_updated)}</td>
        <td>${esc(r.supt_vendor)}</td><td>${badgePii(r.contains_pii)}</td><td>${badgeIso(r.iso_classification)}</td>
        ${actionsCell(empActions(r, 'monitors'))}</tr>`).join('');
      return;
    }

    thead.innerHTML = `<tr>
      <th>Asset Type</th><th>Manufacturer</th><th>Model</th><th>P/N</th><th>Asset Owner</th><th>Assigned To</th>
      <th>Asset Status</th><th>Dept</th><th>Location</th><th>Warranty</th><th>Install Date</th>
      <th>Date Added/Updated</th><th>Supt Vendor</th><th>Linked Device</th><th>Contains PII</th><th>ISO Class</th><th>Actions</th></tr>`;
    tbody.innerHTML = rows.map((r) => `<tr>
      <td>${esc(r.asset_type)}</td><td>${esc(r.asset_manufacturer)}</td><td>${esc(r.model)}</td><td>${esc(r.pn)}</td>
      <td>${esc(r.asset_owner)}</td><td>${esc(r.assigned_to)}</td><td>${badgeStatusAsset(r.asset_status)}</td>
      <td>${esc(r.dept)}</td><td>${formatLocationDisplay(r.location)}</td><td>${esc(r.warranty)}</td>
      <td>${esc(r.install_date)}</td><td>${esc(r.date_added_updated)}</td><td>${esc(r.supt_vendor)}</td>
      <td>${esc(r.linked_device_tag)}</td><td>${badgePii(r.contains_pii)}</td><td>${badgeIso(r.iso_classification)}</td>
      ${actionsCell(empActions(r, 'accessories'))}</tr>`).join('');
  }

  function admActions(r, table) {
    return `<button type="button" class="link" data-act="edit" data-table="${table}" data-id="${r.id}">Edit</button>
      <button type="button" class="link" data-act="del" data-table="${table}" data-id="${r.id}">Delete</button>`;
  }

  function renderAdminTable(rows) {
    const thead = $('#data-thead');
    const tbody = $('#data-tbody');
    const ch = state.admChip;

    if (ch === 'all') {
      thead.innerHTML = `<tr>
        <th>Category</th><th>Asset Type</th><th>Device ID</th><th>Location</th><th>Model</th>
        <th>Dept</th><th>Asset Owner</th><th>Contains PII</th><th>ISO Class</th><th>Actions</th></tr>`;
      tbody.innerHTML = rows.map((r) => `<tr>
        <td>${esc(catLabel(r.__table))}</td><td>${esc(r.asset_type)}</td><td>${esc(r.device_id)}</td>
        <td>${formatLocationDisplay(r.location)}</td><td>${esc(r.model)}</td><td>${esc(r.dept)}</td>
        <td>${esc(r.asset_owner)}</td><td>${badgePii(r.contains_pii)}</td><td>${badgeIso(r.iso_classification)}</td>
        ${actionsCell(admActions(r, r.__table))}</tr>`).join('');
      return;
    }

    if (ch === 'ups') {
      thead.innerHTML = `<tr>
        <th>Asset Type</th><th>Device ID</th><th>Location</th><th>Model</th><th>Warranty</th>
        <th>Install Date</th><th>Supt Vendor</th><th>Dept</th><th>Asset Owner</th>
        <th>Contains PII</th><th>Date Added/Updated</th><th>ISO Class</th><th>Actions</th></tr>`;
      tbody.innerHTML = rows.map((r) => `<tr>
        <td>${esc(r.asset_type)}</td><td>${esc(r.device_id)}</td><td>${formatLocationDisplay(r.location)}</td>
        <td>${esc(r.model)}</td><td>${esc(r.warranty)}</td><td>${esc(r.install_date)}</td>
        <td>${esc(r.supt_vendor)}</td><td>${esc(r.dept)}</td><td>${esc(r.asset_owner)}</td>
        <td>${badgePii(r.contains_pii)}</td><td>${esc(r.date_added_updated)}</td><td>${badgeIso(r.iso_classification)}</td>
        ${actionsCell(admActions(r, 'ups'))}</tr>`).join('');
      return;
    }

    if (ch === 'mobile') {
      thead.innerHTML = `<tr>
        <th>Asset Type</th><th>Device ID</th><th>Location</th><th>Model</th><th>P/N</th>
        <th>Warranty</th><th>Supt Vendor</th><th>Dept</th><th>Asset Owner</th>
        <th>Contains PII</th><th>Date Added/Updated</th><th>ISO Class</th><th>Actions</th></tr>`;
      tbody.innerHTML = rows.map((r) => `<tr>
        <td>${esc(r.asset_type)}</td><td>${esc(r.device_id)}</td><td>${formatLocationDisplay(r.location)}</td>
        <td>${esc(r.model)}</td><td>${esc(r.pn)}</td><td>${esc(r.warranty)}</td><td>${esc(r.supt_vendor)}</td>
        <td>${esc(r.dept)}</td><td>${esc(r.asset_owner)}</td><td>${badgePii(r.contains_pii)}</td>
        <td>${esc(r.date_added_updated)}</td><td>${badgeIso(r.iso_classification)}</td>
        ${actionsCell(admActions(r, 'mobile_phones'))}</tr>`).join('');
      return;
    }

    if (ch === 'scanner') {
      thead.innerHTML = `<tr>
        <th>Asset Type</th><th>Device ID</th><th>Location</th><th>Model</th><th>Service Tag</th>
        <th>P/N</th><th>Warranty</th><th>Supt Vendor</th><th>Dept</th><th>Description</th>
        <th>Asset Owner</th><th>Contains PII</th><th>Date Added/Updated</th><th>ISO Class</th><th>Actions</th></tr>`;
      tbody.innerHTML = rows.map((r) => `<tr>
        <td>${esc(r.asset_type)}</td><td>${esc(r.device_id)}</td><td>${formatLocationDisplay(r.location)}</td>
        <td>${esc(r.model)}</td><td>${esc(r.service_tag)}</td><td>${esc(r.pn)}</td><td>${esc(r.warranty)}</td>
        <td>${esc(r.supt_vendor)}</td><td>${esc(r.dept)}</td><td>${esc(r.description)}</td>
        <td>${esc(r.asset_owner)}</td><td>${badgePii(r.contains_pii)}</td><td>${esc(r.date_added_updated)}</td>
        <td>${badgeIso(r.iso_classification)}</td>
        ${actionsCell(admActions(r, 'scanners_printers'))}</tr>`).join('');
      return;
    }

    thead.innerHTML = `<tr>
      <th>Asset Type</th><th>Location</th><th>Invoice No</th><th>Warranty</th><th>Install Date</th>
      <th>Supt Vendor</th><th>Dept</th><th>Asset Owner</th><th>Contains PII</th>
      <th>Date Added/Updated</th><th>ISO Class</th><th>Actions</th></tr>`;
    const frows = ch === 'camera' ? rows.filter((r) => {
      const at = String(r.asset_type || '').toLowerCase();
      return at.includes('camera') || at.includes('dvr');
    }) : rows;
    tbody.innerHTML = frows.map((r) => `<tr>
      <td>${esc(r.asset_type)}</td><td>${formatLocationDisplay(r.location)}</td><td>${esc(r.invoice_no)}</td>
      <td>${esc(r.warranty)}</td><td>${esc(r.install_date)}</td><td>${esc(r.supt_vendor)}</td>
      <td>${esc(r.dept)}</td><td>${esc(r.asset_owner)}</td><td>${badgePii(r.contains_pii)}</td>
      <td>${esc(r.date_added_updated)}</td><td>${badgeIso(r.iso_classification)}</td>
      ${actionsCell(admActions(r, 'cameras_dvr'))}</tr>`).join('');
  }

  function renderNetworkingTable(rows) {
    const thead = $('#data-thead');
    const tbody = $('#data-tbody');
    thead.innerHTML = `<tr>
      <th>Asset Type</th><th>Asset ID</th><th>MAC ID</th><th>Asset Owner</th><th>Location</th>
      <th>Model</th><th>S/N</th><th>P/N</th><th>Warranty</th><th>Install Date</th><th>O/S</th>
      <th>Supt Vendor</th><th>Dept</th><th>Configuration</th><th>Contains PII</th>
      <th>Date Added/Updated</th><th>ISO Class</th><th>Actions</th></tr>`;
    rows.forEach((r) => { r.__table = 'networking'; });
    tbody.innerHTML = rows.map((r) => `<tr>
      <td>${esc(r.asset_type)}</td><td>${esc(r.asset_id)}</td><td>${esc(r.mac_id)}</td><td>${esc(r.asset_owner)}</td>
      <td>${formatLocationDisplay(r.location)}</td><td>${esc(r.model)}</td><td>${esc(r.sn)}</td><td>${esc(r.pn)}</td>
      <td>${esc(r.warranty)}</td><td>${esc(r.install_date)}</td><td>${esc(r.os)}</td><td>${esc(r.supt_vendor)}</td>
      <td>${esc(r.dept)}</td><td>${esc(r.configuration)}</td><td>${badgePii(r.contains_pii)}</td>
      <td>${esc(r.date_added_updated)}</td><td>${badgeIso(r.iso_classification)}</td>
      ${actionsCell(`<button type="button" class="link" data-act="edit" data-table="networking" data-id="${r.id}">Edit</button>
        <button type="button" class="link" data-act="del" data-table="networking" data-id="${r.id}">Delete</button>`)}</tr>`).join('');
  }

  function renderCloudTable(rows) {
    const thead = $('#data-thead');
    const tbody = $('#data-tbody');
    thead.innerHTML = `<tr>
      <th>Asset</th><th>Asset Type</th><th>Asset Value</th><th>Asset Owner</th><th>Asset Location</th>
      <th>Contains PII</th><th>Asset Region</th><th>Date Added/Updated</th><th>ISO Class</th><th>Actions</th></tr>`;
    rows.forEach((r) => { r.__table = 'cloud_assets'; });
    tbody.innerHTML = rows.map((r) => `<tr>
      <td>${esc(r.asset)}</td><td>${esc(r.asset_type)}</td><td>${esc(r.asset_value)}</td><td>${esc(r.asset_owner)}</td>
      <td>${formatLocationDisplay(r.asset_location)}</td><td>${badgePii(r.contains_pii)}</td><td>${esc(r.asset_region)}</td>
      <td>${esc(r.date_added_updated)}</td><td>${badgeIso(r.iso_classification)}</td>
      ${actionsCell(`<button type="button" class="link" data-act="edit" data-table="cloud_assets" data-id="${r.id}">Edit</button>
        <button type="button" class="link" data-act="del" data-table="cloud_assets" data-id="${r.id}">Delete</button>`)}</tr>`).join('');
  }

  function renderInfodeskTable(rows) {
    const thead = $('#data-thead');
    const tbody = $('#data-tbody');
    thead.innerHTML = `<tr>
      <th>Asset</th><th>Asset Type</th><th>Asset Value</th><th>Asset Owner</th><th>Asset Location</th>
      <th>Contains PII</th><th>Date Added/Updated</th><th>ISO Class</th><th>Actions</th></tr>`;
    rows.forEach((r) => { r.__table = 'infodesk_applications'; });
    tbody.innerHTML = rows.map((r) => `<tr>
      <td>${esc(r.asset)}</td><td>${esc(r.asset_type)}</td><td>${esc(r.asset_value)}</td><td>${esc(r.asset_owner)}</td>
      <td>${formatLocationDisplay(r.asset_location)}</td><td>${badgePii(r.contains_pii)}</td>
      <td>${esc(r.date_added_updated)}</td><td>${badgeIso(r.iso_classification)}</td>
      ${actionsCell(`<button type="button" class="link" data-act="edit" data-table="infodesk_applications" data-id="${r.id}">Edit</button>
        <button type="button" class="link" data-act="del" data-table="infodesk_applications" data-id="${r.id}">Delete</button>`)}</tr>`).join('');
  }

  function renderThirdPartyTable(rows) {
    const thead = $('#data-thead');
    const tbody = $('#data-tbody');
    thead.innerHTML = `<tr>
      <th>Asset</th><th>Asset Type</th><th>Asset Value</th><th>Asset Owner</th><th>Asset Location</th>
      <th>Contains PII</th><th>Date Added/Updated</th><th>CVE Alert</th><th>Setup</th><th>Billing API</th>
      <th>Patch Status</th><th>ISO Class</th><th>Actions</th></tr>`;
    rows.forEach((r) => { r.__table = 'third_party_software'; });
    tbody.innerHTML = rows.map((r) => `<tr>
      <td>${esc(r.asset)}</td><td>${esc(r.asset_type)}</td><td>${esc(r.asset_value)}</td><td>${esc(r.asset_owner)}</td>
      <td>${formatLocationDisplay(r.asset_location)}</td><td>${badgePii(r.contains_pii)}</td><td>${esc(r.date_added_updated)}</td>
      <td>${badgeCve(r.cve_alert)}</td><td>${esc(r.setup)}</td><td>${esc(r.billing_api)}</td><td>${badgePatch(r.patch_status)}</td>
      <td>${badgeIso(r.iso_classification)}</td>
      ${actionsCell(`<button type="button" class="link" data-act="edit" data-table="third_party_software" data-id="${r.id}">Edit</button>
        <button type="button" class="link" data-act="del" data-table="third_party_software" data-id="${r.id}">Delete</button>`)}</tr>`).join('');
  }

  function renderGatepassTable(rows) {
    const thead = $('#data-thead');
    const tbody = $('#data-tbody');
    thead.innerHTML = `<tr>
      <th>Gatepass No</th><th>Date</th><th>Pass Type</th><th>Issued To</th><th>Person</th>
      <th>Dept Head</th><th>Security Guard</th><th>Expected Return</th><th>Status</th><th>Actions</th></tr>`;
    rows.forEach((r) => { r.__table = 'gatepass'; });
    tbody.innerHTML = rows.map((r) => `<tr>
      <td>${esc(r.gatepass_no)}</td><td>${esc(r.gatepass_date)}</td><td>${esc(r.pass_type)}</td>
      <td>${esc(r.issued_to)}</td><td>${esc(r.person)}</td><td>${esc(r.dept_head)}</td><td>${esc(r.security_guard)}</td>
      <td>${esc(r.expected_return_date)}</td><td>${badgeGatepassStatus(r.status)}</td>
      ${actionsCell(`<button type="button" class="link" data-act="edit" data-table="gatepass" data-id="${r.id}">Edit</button>
        <button type="button" class="link" data-act="del" data-table="gatepass" data-id="${r.id}">Delete</button>
        <button type="button" class="link" data-act="pdf-gp" data-id="${r.id}">Download PDF</button>
        <button type="button" class="link" data-act="print-gp" data-id="${r.id}">Print</button>`)}</tr>`).join('');
  }

  function renderLeaversTable(rows) {
    const thead = $('#data-thead');
    const tbody = $('#data-tbody');
    thead.innerHTML = `<tr>
      <th>Employee Name</th><th>Date of Leaving</th><th>Dept</th><th>Line Manager</th>
      <th>Overall Status</th><th>Evidence</th><th>Actions</th></tr>`;
    rows.forEach((r) => { r.__table = 'leavers_checklist'; });
    tbody.innerHTML = rows.map((r) => {
      const hasEv = !!(r.evidence_file_s3_key);
      const evCell = hasEv
        ? `<span class="badge badge-ev-yes" data-act="view-ev" data-id="${r.id}" role="button" tabindex="0">Evidence uploaded</span>`
        : `<span class="badge badge-ev-none">No evidence</span>`;
      return `<tr>
        <td>${esc(r.employee_name)}</td><td>${esc(r.date_of_leaving)}</td><td>${esc(r.department)}</td>
        <td>${esc(r.line_manager)}</td><td>${badgeOverall(r.overall_status)}</td><td>${evCell}</td>
        ${actionsCell(`<button type="button" class="link" data-act="view-leaver" data-id="${r.id}">View Checklist</button>
          <button type="button" class="link" data-act="edit" data-table="leavers_checklist" data-id="${r.id}">Edit</button>
          <button type="button" class="link" data-act="pdf-lv" data-id="${r.id}">Download PDF</button>
          <button type="button" class="link" data-act="del" data-table="leavers_checklist" data-id="${r.id}">Delete</button>`)}</tr>`;
    }).join('');
  }

  function renderAuditTable() {
    const thead = $('#data-thead');
    const tbody = $('#data-tbody');
    thead.innerHTML = `<tr>
      <th>Timestamp</th><th>Table</th><th>Record ID</th><th>Action</th><th>Changed Fields</th>
      <th>Old Values</th><th>New Values</th><th>Performed By</th><th>IP Address</th><th>Ref</th></tr>`;
    const rows = state.auditItems;
    tbody.innerHTML = rows.map((r) => `<tr>
      <td>${esc(r.performed_at)}</td><td>${esc(r.table_name)}</td><td>${esc(r.record_id)}</td><td>${esc(r.action)}</td>
      <td>${esc(r.changed_fields)}</td><td>${esc(r.old_values)}</td><td>${esc(r.new_values)}</td>
      <td>${esc(r.performed_by)}</td><td>${esc(r.ip_address)}</td><td>${esc(r.iso_ref)}</td></tr>`).join('');
  }

  function setFiltersVisible(show) {
    $('#filters-bar').style.display = show ? 'flex' : 'none';
    $('#active-filters').style.display = show ? 'flex' : 'none';
    if (!show) $('#result-bar').hidden = true;
  }

  function updateToolbar() {
    const ex = $('#toolbar-extra');
    ex.innerHTML = '';
    if (state.tab === 'gatepass') {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'btn btn-export';
      b.textContent = '↓ Export Gatepass';
      b.addEventListener('click', () => { window.location.href = '/api/gatepass/export'; });
      ex.appendChild(b);
    }
    if (state.tab === 'leavers') {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'btn btn-export';
      b.textContent = '↓ Export Leavers';
      b.addEventListener('click', () => { window.location.href = '/api/leavers/export'; });
      ex.appendChild(b);
    }
    if (state.tab === 'audit') {
      ex.innerHTML = `<label class="chips-label">Table</label>
        <input type="text" id="audit-filter-table" class="filter-search" placeholder="table_name" style="min-width:120px" />
        <label class="chips-label">From</label><input type="date" id="audit-from" class="filter-search" style="min-width:140px" />
        <label class="chips-label">To</label><input type="date" id="audit-to" class="filter-search" style="min-width:140px" />
        <button type="button" class="btn btn-primary" id="audit-apply">Apply</button>`;
      $('#audit-apply').addEventListener('click', () => { state.auditPage = 1; loadAuditPage(); });
    }
  }

  async function loadAuditPage() {
    const table = ($('#audit-filter-table') && $('#audit-filter-table').value) || '';
    const fromD = ($('#audit-from') && $('#audit-from').value) || '';
    const toD = ($('#audit-to') && $('#audit-to').value) || '';
    const params = new URLSearchParams({
      page: String(state.auditPage),
      limit: '50',
    });
    if (table) params.set('table', table);
    if (fromD) params.set('from_date', fromD);
    if (toD) params.set('to_date', toD);
    const data = await api(`/api/audit-log?${params}`);
    state.auditItems = data.items || [];
    state.auditTotal = data.total || 0;
    renderAuditTable();
    const pag = $('#audit-pagination');
    pag.hidden = false;
    $('#audit-page-label').textContent = `Page ${state.auditPage} · ${state.auditTotal} rows`;
    $('#audit-prev').disabled = state.auditPage <= 1;
    $('#audit-next').disabled = state.auditPage * 50 >= state.auditTotal;
  }

  function renderTable() {
    $('#audit-pagination').hidden = state.tab !== 'audit';
    if (state.tab === 'audit') {
      renderAuditTable();
      return;
    }
    const raw = currentRawRows();
    const filtered = applyFilters(raw, false, false);
    rebuildDeptFilter();
    rebuildLocationFilter();
    renderActiveFilterChips();
    locationResultBar(filtered);

    switch (state.tab) {
      case 'employee':
        renderEmployeeTable(filtered);
        break;
      case 'admin':
        renderAdminTable(filtered);
        break;
      case 'networking':
        renderNetworkingTable(filtered);
        break;
      case 'cloud':
        renderCloudTable(filtered);
        break;
      case 'infodesk':
        renderInfodeskTable(filtered);
        break;
      case 'third_party':
        renderThirdPartyTable(filtered);
        break;
      case 'gatepass':
        renderGatepassTable(filtered);
        break;
      case 'leavers':
        renderLeaversTable(filtered);
        break;
      default:
        break;
    }
    wireTableBody();
  }

  let tableWired = false;
  function wireTableBody() {
    if (tableWired) return;
    tableWired = true;
    $('#data-tbody').addEventListener('click', onTableClick);
  }

  async function onTableClick(e) {
    const t = e.target.closest('[data-act]');
    if (!t) return;
    const act = t.getAttribute('data-act');
    const id = parseInt(t.getAttribute('data-id') || '0', 10);
    const tbl = t.getAttribute('data-table');
    if (act === 'edit' && tbl) {
      openEditModal(tbl, id);
    }
    if (act === 'del' && tbl) {
      if (!confirm('Delete this record?')) return;
      try {
        await api(`/api/${tbl}/${id}`, { method: 'DELETE' });
        showToast('Deleted');
        await loadTabData();
        renderTable();
        await loadStats();
      } catch (err) {
        showToast(String(err.message));
      }
    }
    if (act === 'pdf-gp' && id) {
      window.open(`/api/gatepass/${id}/pdf`, '_blank');
    }
    if (act === 'print-gp' && id) {
      window.open(`/api/gatepass/${id}/pdf`, '_blank');
    }
    if (act === 'pdf-lv' && id) {
      window.open(`/api/leavers/${id}/pdf`, '_blank');
    }
    if (act === 'view-ev' && id) {
      try {
        const j = await api(`/api/leavers/${id}/evidence`);
        if (j.url) window.open(j.url, '_blank');
      } catch (err) {
        showToast(String(err.message));
      }
    }
    if (act === 'view-leaver' && id) {
      const row = state.rawLeavers.find((x) => x.id === id);
      if (row) openLeaverPanel(row);
    }
  }

  async function loadStats() {
    try {
      state.stats = await api('/api/stats');
      const s = state.stats;
      const emp = (s.laptops || 0) + (s.desktops || 0) + (s.monitors || 0) + (s.accessories || 0);
      const adm = (s.ups || 0) + (s.mobile_phones || 0) + (s.scanners_printers || 0) + (s.cameras_dvr || 0);
      document.querySelectorAll('[data-tab-count="employee"]').forEach((el) => { el.textContent = emp; });
      document.querySelectorAll('[data-tab-count="networking"]').forEach((el) => { el.textContent = s.networking || 0; });
      document.querySelectorAll('[data-tab-count="cloud"]').forEach((el) => { el.textContent = s.cloud_assets || 0; });
      document.querySelectorAll('[data-tab-count="infodesk"]').forEach((el) => { el.textContent = s.infodesk_applications || 0; });
      document.querySelectorAll('[data-tab-count="third_party"]').forEach((el) => { el.textContent = s.third_party_software || 0; });
      document.querySelectorAll('[data-tab-count="admin"]').forEach((el) => { el.textContent = adm; });
      document.querySelectorAll('[data-tab-count="gatepass"]').forEach((el) => { el.textContent = s.gatepass || 0; });
      document.querySelectorAll('[data-tab-count="leavers"]').forEach((el) => { el.textContent = s.leavers_checklist || 0; });
      document.querySelectorAll('[data-tab-count="audit"]').forEach((el) => { el.textContent = s.audit_log || 0; });
    } catch (_) { /* ignore */ }
  }

  async function loadTabData() {
    if (state.tab === 'employee') {
      const [la, de, mo, ac] = await Promise.all([
        api('/api/laptops'),
        api('/api/desktops'),
        api('/api/monitors'),
        api('/api/accessories'),
      ]);
      state.rawEmployee = [
        ...la.map((r) => ({ ...r, __table: 'laptops' })),
        ...de.map((r) => ({ ...r, __table: 'desktops' })),
        ...mo.map((r) => ({ ...r, __table: 'monitors' })),
        ...ac.map((r) => ({ ...r, __table: 'accessories' })),
      ];
    } else if (state.tab === 'admin') {
      const [u, m, sc, ca] = await Promise.all([
        api('/api/ups'),
        api('/api/mobile_phones'),
        api('/api/scanners_printers'),
        api('/api/cameras_dvr'),
      ]);
      state.rawAdmin = [
        ...u.map((r) => ({ ...r, __table: 'ups' })),
        ...m.map((r) => ({ ...r, __table: 'mobile_phones' })),
        ...sc.map((r) => ({ ...r, __table: 'scanners_printers' })),
        ...ca.map((r) => ({ ...r, __table: 'cameras_dvr' })),
      ];
    } else if (state.tab === 'networking') {
      state.rawNetworking = await api('/api/networking');
    } else if (state.tab === 'cloud') {
      state.rawCloud = await api('/api/cloud_assets');
    } else if (state.tab === 'infodesk') {
      state.rawInfodesk = await api('/api/infodesk_applications');
    } else if (state.tab === 'third_party') {
      state.rawThirdParty = await api('/api/third_party_software');
    } else if (state.tab === 'gatepass') {
      state.rawGatepass = await api('/api/gatepass');
    } else if (state.tab === 'leavers') {
      state.rawLeavers = await api('/api/leavers_checklist');
    } else if (state.tab === 'audit') {
      await loadAuditPage();
    }
  }

  function showModal(title, bodyHtml, onSave) {
    $('#modal-title').textContent = title;
    $('#modal-body').innerHTML = bodyHtml;
    $('#modal-overlay').hidden = false;
    state._modalSave = onSave;
  }

  function hideModal() {
    $('#modal-overlay').hidden = true;
    state.modalMode = null;
    state.editing = null;
    state.gatepassItems = [];
    state.leaverFile = null;
  }

  function fieldText(id, label, val, ph, readOnly) {
    const ro = readOnly ? ' readonly' : '';
    return `<div class="form-field"><label for="${id}">${esc(label)}</label>
      <input id="${id}" value="${esc(val || '')}" placeholder="${esc(ph || '')}"${ro} /></div>`;
  }

  function selectOpts(id, opts, val) {
    return `<select id="${id}">${opts.map((o) =>
      `<option${String(o) === String(val) ? ' selected' : ''}>${o}</option>`).join('')}</select>`;
  }

  function selectOptsHtml(id, opts, val) {
    return selectOpts(id, opts, val);
  }

  function fieldSelect(id, label, options, val) {
    let o = '';
    options.forEach((x) => {
      const sel = String(x) === String(val) ? ' selected' : '';
      o += `<option${sel}>${esc(x)}</option>`;
    });
    return `<div class="form-field"><label for="${id}">${esc(label)}</label>
      <select id="${id}">${o}</select></div>`;
  }

  function fieldArea(id, label, val) {
    return `<div class="form-field full"><label for="${id}">${esc(label)}</label>
      <textarea id="${id}">${esc(val || '')}</textarea></div>`;
  }

  function collectVals(ids) {
    const o = {};
    ids.forEach((id) => {
      const el = document.getElementById(id);
      if (el) o[id] = el.value;
    });
    return o;
  }

  async function openEditModal(table, id) {
    state.editing = { table, id };
    const row = await api(`/api/${table}`).then((rows) => rows.find((r) => r.id === id));
    if (!row) {
      showToast('Record not found');
      return;
    }
    if (table === 'gatepass') {
      openGatepassModal(row);
      return;
    }
    if (table === 'leavers_checklist') {
      openLeaverModal(row);
      return;
    }
    const keys = Object.keys(row).filter((k) => !['id', 'created_at', 'updated_at'].includes(k));
    let html = '<div class="form-grid">';
    keys.forEach((k) => {
      if (k === 'location' || k === 'asset_location' || k === 'hw_inventory_location') {
        const fid = `f_${k}`;
        html += `<div class="form-field full"><label>Office / city</label>${officeSelectHtml(fid, false)}</div>`;
        return;
      }
      html += fieldText(`f_${k}`, k.replace(/_/g, ' '), row[k], '');
    });
    html += fieldText('f_actor', 'Updated by (optional)', '', '');
    html += '</div>';
    showModal(`Edit ${table}`, html, async () => {
      const payload = {};
      keys.forEach((k) => {
        if (k === 'location' || k === 'asset_location' || k === 'hw_inventory_location') {
          const v = document.getElementById(`f_${k}`).value;
          if (v) payload[k] = v;
          return;
        }
        const el = document.getElementById(`f_${k}`);
        if (el && el.value !== '') payload[k] = el.value;
      });
      const actor = document.getElementById('f_actor');
      if (actor && actor.value) payload.updated_by = actor.value;
      try {
        await api(`/api/${table}/${id}`, { method: 'PUT', body: JSON.stringify(payload) });
        showToast('Saved');
        hideModal();
        await loadTabData();
        renderTable();
      } catch (e) {
        showToast(e.message);
      }
    });
    keys.forEach((k) => {
      if (k === 'location' || k === 'asset_location' || k === 'hw_inventory_location') {
        setOfficeSelectValue(`f_${k}`, row[k]);
      }
    });
  }

  function gatepassItemsHtml(items) {
    const rows = (items && items.length) ? items : [{ description: '', unit: '', qty: '', remarks: '' }];
    return rows.map((it, i) => `<tr data-idx="${i}">
      <td>${i + 1}</td><td><input type="text" class="gi-desc" value="${esc(it.description || '')}" /></td>
      <td><input type="text" class="gi-unit" value="${esc(it.unit || '')}" /></td>
      <td><input type="text" class="gi-qty" value="${esc(it.qty || '')}" /></td>
      <td><input type="text" class="gi-rem" value="${esc(it.remarks || '')}" /></td>
      <td><button type="button" class="link gi-rm">×</button></td></tr>`).join('');
  }

  function readGatepassItems() {
    const trs = $$('#gp-items tr');
    return trs.map((tr) => ({
      description: tr.querySelector('.gi-desc')?.value || '',
      unit: tr.querySelector('.gi-unit')?.value || '',
      qty: tr.querySelector('.gi-qty')?.value || '',
      remarks: tr.querySelector('.gi-rem')?.value || '',
    })).filter((x) => x.description || x.unit || x.qty || x.remarks);
  }

  async function openGatepassModal(row) {
    const isNew = !row;
    let gp = row;
    if (isNew) {
      const n = await api('/api/gatepass/next-number');
      gp = { gatepass_no: n.gatepass_no, pass_type: 'Returnable', status: 'Open' };
    }
    let items = [];
    try {
      items = gp.asset_items ? JSON.parse(gp.asset_items) : [];
    } catch (_) { items = []; }
    if (!Array.isArray(items)) items = [];
    state.gatepassItems = items;

    const html = `<div class="form-grid">
      ${fieldText('gp_no', 'Gatepass No', gp.gatepass_no, '', true)}
      ${fieldText('gp_date', 'Gatepass Date', gp.gatepass_date || new Date().toISOString().slice(0, 10), '')}
      ${fieldSelect('gp_pt', 'Pass Type', ['Returnable', 'Temporary', 'Permanent'], gp.pass_type)}
      ${fieldText('gp_issued', 'Issued To', gp.issued_to, '')}
      ${fieldText('gp_person', 'Person', gp.person, '')}
      ${fieldText('gp_dh', 'Dept Head', gp.dept_head, '')}
      ${fieldText('gp_sg', 'Security Guard', gp.security_guard, '')}
      ${fieldText('gp_recv', 'Receiver Name', gp.receiver_name, '')}
      <div class="form-field full" id="gp-er-wrap">${fieldText('gp_er', 'Expected Return', gp.expected_return_date, '')}</div>
      ${fieldSelect('gp_st', 'Status', ['Open', 'Closed', 'Cancelled'], gp.status)}
      ${fieldArea('gp_rm', 'Remarks', gp.remarks)}
      ${fieldText('gp_actor', 'Updated by (optional)', '', '')}
      </div>
      <p class="section-title">Items</p>
      <table class="items-editor" id="gp-items-wrap"><thead><tr><th>Sr</th><th>Description</th><th>Unit</th><th>Qty</th><th>Remarks</th><th></th></tr></thead>
      <tbody id="gp-items">${gatepassItemsHtml(state.gatepassItems)}</tbody></table>
      <button type="button" class="btn btn-ghost" id="gp-add-row">+ Add Row</button>`;

    showModal(isNew ? 'Add Gatepass' : 'Edit Gatepass', html, async () => {
      const payload = {
        gatepass_no: document.getElementById('gp_no').value,
        gatepass_date: document.getElementById('gp_date').value,
        pass_type: document.getElementById('gp_pt').value,
        issued_to: document.getElementById('gp_issued').value,
        person: document.getElementById('gp_person').value,
        dept_head: document.getElementById('gp_dh').value,
        security_guard: document.getElementById('gp_sg').value,
        receiver_name: document.getElementById('gp_recv').value,
        expected_return_date: document.getElementById('gp_er') ? document.getElementById('gp_er').value : '',
        status: document.getElementById('gp_st').value,
        remarks: document.getElementById('gp_rm').value,
        asset_items: JSON.stringify(readGatepassItems()),
      };
      const act = document.getElementById('gp_actor');
      if (act && act.value) payload.updated_by = act.value;
      try {
        if (isNew) {
          await api('/api/gatepass', { method: 'POST', body: JSON.stringify(payload) });
        } else {
          await api(`/api/gatepass/${row.id}`, { method: 'PUT', body: JSON.stringify(payload) });
        }
        showToast('Saved');
        hideModal();
        await loadTabData();
        renderTable();
        await loadStats();
      } catch (e) {
        showToast(e.message);
      }
    });

    document.getElementById('gp-add-row').addEventListener('click', () => {
      const tb = $('#gp-items');
      const i = tb.querySelectorAll('tr').length;
      tb.insertAdjacentHTML('beforeend', `<tr data-idx="${i}">
        <td>${i + 1}</td><td><input type="text" class="gi-desc" /></td>
        <td><input type="text" class="gi-unit" /></td><td><input type="text" class="gi-qty" /></td>
        <td><input type="text" class="gi-rem" /></td><td><button type="button" class="link gi-rm">×</button></td></tr>`);
    });
    $('#gp-items-wrap').addEventListener('click', (e) => {
      if (e.target.classList.contains('gi-rm')) e.target.closest('tr').remove();
    });
    const pt = document.getElementById('gp_pt');
    const erWrap = document.getElementById('gp-er-wrap');
    function syncEr() {
      const v = pt.value;
      erWrap.style.display = (v === 'Permanent') ? 'none' : '';
    }
    pt.addEventListener('change', syncEr);
    syncEr();
  }

  function openGatepassModalNew() {
    openGatepassModal(null);
  }

  function leaverSystemsHtml(row) {
    return `<table class="systems-table" id="lv-sys"><thead><tr><th>System Name</th><th>Status</th></tr></thead><tbody>
      ${SYSTEM_LABELS.map(([label, key]) => {
        const v = row[key] || 'Active';
        const opts = ['Active', 'Revoked', 'N/A'].map((o) =>
          `<option${o === v ? ' selected' : ''}>${o}</option>`).join('');
        return `<tr class="row-sys-${String(v).toLowerCase().replace(/\s+/g, '')}" data-key="${key}">
          <td>${esc(label)}</td><td><select class="lv-sys-sel">${opts}</select></td></tr>`;
      }).join('')}
    </tbody></table>`;
  }

  function refreshSysRowColors() {
    $$('#lv-sys tbody tr').forEach((tr) => {
      const sel = tr.querySelector('.lv-sys-sel');
      const v = sel.value;
      tr.className = v === 'Active' ? 'row-sys-active' : v === 'Revoked' ? 'row-sys-revoked' : 'row-sys-na';
    });
  }

  async function openLeaverModal(row) {
    const isNew = !row;
    const c = row || {
      employee_name: '', date_of_leaving: '', department: '', line_manager: '', email_address: '',
      hw_handed_over: 'Pending', hw_inventory_location: '', communication_github_ticket: '', notes: '',
      overall_status: 'In Progress',
    };
    SYSTEM_KEYS.forEach((k) => { if (c[k] == null) c[k] = 'Active'; });

    const html = `
      <div class="section-title">Employee details</div>
      <div class="form-grid">
        ${fieldText('lv_name', 'Employee Name *', c.employee_name, '')}
        ${fieldText('lv_leave', 'Date of Leaving *', c.date_of_leaving, '')}
        ${fieldText('lv_dept', 'Department', c.department, '')}
        ${fieldText('lv_mgr', 'Line Manager', c.line_manager, '')}
        ${fieldText('lv_email', 'Email Address', c.email_address, '')}
        ${fieldText('lv_ticket', 'Communication / GitHub Ticket', c.communication_github_ticket, '')}
        ${fieldText('lv_actor', 'Updated by (optional)', '', '')}
      </div>
      ${fieldArea('lv_notes', 'Notes', c.notes)}
      <div class="section-title">System access</div>
      <button type="button" class="btn btn-ghost" id="lv-revoke-all">Revoke All</button>
      ${leaverSystemsHtml(c)}
      <div class="section-title">Hardware</div>
      <div class="form-grid">
        ${fieldSelect('lv_hw', 'HW Handed Over at Location?', ['Pending', 'Yes', 'No'], c.hw_handed_over)}
        <div class="form-field full"><label>HW handover office / city</label>${officeSelectHtml('lv_hwloc', false)}</div>
      </div>
      <div class="section-title">Evidence</div>
      <div class="dropzone" id="lv-drop">${isNew ? 'Save record first to upload evidence.' : 'Drop file or click (PDF, JPG, PNG, DOCX, max 10MB)'}</div>
      <input type="file" id="lv-file" hidden accept=".pdf,.jpg,.jpeg,.png,.docx" />
      <div class="section-title">Sign-offs</div>
      <table class="signoff-table"><thead><tr><th>Sign-off</th><th>Name</th><th>Status</th><th>Date</th></tr></thead><tbody>
        <tr><td>IT Peer Review</td><td><input id="lv_ipn" value="${esc(c.it_peer_reviewer || '')}" /></td>
          <td>${selectOpts('lv_ips', ['Pending', 'Approved', 'Rejected'], c.it_peer_review)}</td>
          <td><input type="date" id="lv_ipd" value="${esc(String(c.it_peer_review_date || '').slice(0, 10))}" /></td></tr>
        <tr><td>Reporting Manager</td><td><input id="lv_rmn" value="${esc(c.reporting_manager_name || '')}" /></td>
          <td>${selectOptsHtml('lv_rms', ['Pending', 'Approved', 'Rejected'], c.reporting_manager)}</td>
          <td><input type="date" id="lv_rmd" value="${esc(String(c.reporting_manager_date || '').slice(0, 10))}" /></td></tr>
        <tr><td>Confirmation Audit</td><td><input id="lv_can" value="${esc(c.confirmation_audit_by || '')}" /></td>
          <td>${selectOptsHtml('lv_cas', ['Pending', 'Approved', 'Rejected'], c.confirmation_audit)}</td>
          <td><input type="date" id="lv_cad" value="${esc(String(c.confirmation_audit_date || '').slice(0, 10))}" /></td></tr>
      </tbody></table>`;

    showModal(isNew ? 'Add Leaver' : 'Edit Leaver', html, async () => {
      const payload = {
        employee_name: document.getElementById('lv_name').value,
        date_of_leaving: document.getElementById('lv_leave').value,
        department: document.getElementById('lv_dept').value,
        line_manager: document.getElementById('lv_mgr').value,
        email_address: document.getElementById('lv_email').value,
        communication_github_ticket: document.getElementById('lv_ticket').value,
        notes: document.getElementById('lv_notes').value,
        hw_handed_over: document.getElementById('lv_hw').value,
        hw_inventory_location: document.getElementById('lv_hwloc').value,
        it_peer_reviewer: document.getElementById('lv_ipn').value,
        it_peer_review: document.getElementById('lv_ips').value,
        it_peer_review_date: document.getElementById('lv_ipd').value,
        reporting_manager_name: document.getElementById('lv_rmn').value,
        reporting_manager: document.getElementById('lv_rms').value,
        reporting_manager_date: document.getElementById('lv_rmd').value,
        confirmation_audit_by: document.getElementById('lv_can').value,
        confirmation_audit: document.getElementById('lv_cas').value,
        confirmation_audit_date: document.getElementById('lv_cad').value,
      };
      SYSTEM_LABELS.forEach(([, key]) => {
        const tr = document.querySelector(`#lv-sys tr[data-key="${key}"]`);
        if (tr) payload[key] = tr.querySelector('.lv-sys-sel').value;
      });
      const merged = { ...c, ...payload };
      payload.overall_status = deriveOverallStatus(merged);
      const act = document.getElementById('lv_actor');
      if (act && act.value) payload.updated_by = act.value;
      try {
        let newId = row && row.id;
        if (isNew) {
          const created = await api('/api/leavers_checklist', { method: 'POST', body: JSON.stringify(payload) });
          newId = created.id;
        } else {
          await api(`/api/leavers_checklist/${row.id}`, { method: 'PUT', body: JSON.stringify(payload) });
        }
        const f = document.getElementById('lv-file').files[0];
        if (f && newId) {
          const fd = new FormData();
          fd.append('file', f);
          if (act && act.value) fd.append('updated_by', act.value);
          const r = await fetch(`/api/leavers/${newId}/upload-evidence`, { method: 'POST', body: fd });
          if (!r.ok) {
            let msg = 'Upload failed';
            try {
              const j = await r.json();
              if (j.detail) msg = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
            } catch (_) { /* ignore */ }
            throw new Error(msg);
          }
        }
        showToast('Saved');
        hideModal();
        await loadTabData();
        renderTable();
        await loadStats();
      } catch (e) {
        showToast(e.message);
      }
    });

    setOfficeSelectValue('lv_hwloc', c.hw_inventory_location);
    $('#lv-sys').addEventListener('change', refreshSysRowColors);
    refreshSysRowColors();
    $('#lv-revoke-all').addEventListener('click', () => {
      $$('#lv-sys .lv-sys-sel').forEach((s) => { s.value = 'Revoked'; });
      refreshSysRowColors();
    });

    if (!isNew) {
      const dz = $('#lv-drop');
      const fi = $('#lv-file');
      dz.addEventListener('click', () => fi.click());
      dz.addEventListener('dragover', (e) => { e.preventDefault(); dz.classList.add('drag'); });
      dz.addEventListener('dragleave', () => dz.classList.remove('drag'));
      dz.addEventListener('drop', (e) => {
        e.preventDefault();
        dz.classList.remove('drag');
        if (e.dataTransfer.files[0]) fi.files = e.dataTransfer.files;
      });
    }
  }

  function sysSym(v) {
    const x = String(v || '').trim();
    if (x === 'Revoked') return '✓';
    if (x === 'N/A') return '—';
    return '✗';
  }

  function openLeaverPanel(c) {
    const { done, total, pct } = calcProgress(c);
    $('#panel-title').textContent = 'IT exit checklist';
    let sysHtml = '<ul class="checklist-list">';
    SYSTEM_LABELS.forEach(([label, key]) => {
      const v = String(c[key] || '').trim();
      sysHtml += `<li>${esc(sysSym(v))} ${esc(label)} — ${esc(v)}</li>`;
    });
    sysHtml += '</ul>';
    const evName = c.evidence_file_name || '—';
    const evBtn = c.evidence_file_s3_key
      ? `<button type="button" class="btn btn-primary" id="pl-ev">View ↗</button>` : '';
    $('#panel-body').innerHTML = `<div class="checklist-doc">
      <p><strong>IT EXIT CHECKLIST — InfoDesk India Pvt Ltd</strong></p>
      <p>Employee: ${esc(c.employee_name)} &nbsp; Date of Leaving: ${esc(c.date_of_leaving)}</p>
      <p>Department: ${esc(c.department)} &nbsp; Line Manager: ${esc(c.line_manager)}</p>
      <p>Email: ${esc(c.email_address)}</p>
      <hr/>
      <p><strong>System access</strong></p>${sysHtml}
      <hr/>
      <p><strong>Hardware</strong></p>
      <p>HW Handed Over: ${esc(c.hw_handed_over)} &nbsp; Location: ${formatLocationDisplay(c.hw_inventory_location)}</p>
      <p>Evidence: ${esc(evName)} ${evBtn}</p>
      <hr/>
      <p><strong>Sign-offs</strong></p>
      <p>IT Peer Review: ${esc(c.it_peer_reviewer)} — ${esc(c.it_peer_review)} ${esc(c.it_peer_review_date || '')}</p>
      <p>Reporting Manager: ${esc(c.reporting_manager_name)} — ${esc(c.reporting_manager)} ${esc(c.reporting_manager_date || '')}</p>
      <p>Confirmation Audit: ${esc(c.confirmation_audit_by)} — ${esc(c.confirmation_audit)} ${esc(c.confirmation_audit_date || '')}</p>
      <hr/>
      <p>GitHub Ticket: ${esc(c.communication_github_ticket)}</p>
      <div class="progress-wrap"><div class="progress-bar"><div style="width:${pct}%"></div></div>
      <p>${done} of ${total} completed (${pct}%)</p></div>
    </div>`;
    $('#panel-overlay').hidden = false;
    const evb = document.getElementById('pl-ev');
    if (evb) {
      evb.addEventListener('click', async () => {
        try {
          const j = await api(`/api/leavers/${c.id}/evidence`);
          if (j.url) window.open(j.url, '_blank');
        } catch (e) {
          showToast(e.message);
        }
      });
    }
  }

  function hidePanel() {
    $('#panel-overlay').hidden = true;
  }

  const SIMPLE_CREATE_DEFAULTS = {
    networking: {
      asset_type: '', asset_id: '', mac_id: '', asset_owner: '', location: '', dept: '', model: '', configuration: '',
    },
    cloud_assets: { asset: '', asset_type: '', asset_value: '', asset_owner: '', asset_location: '', asset_region: '' },
    infodesk_applications: { asset: '', asset_type: '', asset_value: '', asset_owner: '', asset_location: '' },
    third_party_software: {
      asset: '', asset_type: '', asset_value: '', asset_owner: '', asset_location: '', cve_alert: 'None', patch_status: 'Up to date',
    },
    laptops: {
      asset_manufacturer: '', service_tag: '', model: '', asset_owner: '', assigned_to: '', dept: '', location: '',
    },
    desktops: {
      asset_manufacturer: '', service_tag: '', model: '', asset_owner: '', assigned_to: '', dept: '', location: '', configuration: '',
    },
    monitors: { asset_manufacturer: '', service_tag: '', model: '', asset_owner: '', assigned_to: '', dept: '', location: '' },
    accessories: {
      asset_type: 'Keyboard', asset_manufacturer: '', model: '', asset_owner: '', assigned_to: '', dept: '', location: '', linked_device_tag: '',
    },
    ups: { device_id: '', location: '', model: '', dept: '', asset_owner: '' },
    mobile_phones: { device_id: '', location: '', model: '', dept: '', asset_owner: '' },
    scanners_printers: { asset_type: 'Printer', device_id: '', location: '', model: '', dept: '', asset_owner: '' },
    cameras_dvr: { asset_type: 'Camera', location: '', dept: '', asset_owner: '' },
  };

  function openSimpleCreate(table, preset) {
    const base = { ...SIMPLE_CREATE_DEFAULTS[table], ...preset };
    let html = '<div class="form-grid">';
    Object.keys(base).forEach((k) => {
      if (k === 'location' || k === 'asset_location') {
        html += `<div class="form-field full"><label>${esc(k.replace(/_/g, ' '))}</label>${officeSelectHtml(`nc_${k}`, false)}</div>`;
      } else {
        html += fieldText(`nc_${k}`, k.replace(/_/g, ' '), base[k], '');
      }
    });
    html += `${fieldText('nc_actor', 'Created by (optional)', '', '')}</div>`;
    showModal(`Add — ${table}`, html, async () => {
      const payload = {};
      Object.keys(base).forEach((k) => {
        if (k === 'location' || k === 'asset_location') {
          const v = document.getElementById(`nc_${k}`).value;
          if (v) payload[k] = v;
        } else {
          const el = document.getElementById(`nc_${k}`);
          if (el && el.value !== '') payload[k] = el.value;
        }
      });
      const actor = document.getElementById('nc_actor');
      if (actor && actor.value) payload.created_by = actor.value;
      try {
        await api(`/api/${table}`, { method: 'POST', body: JSON.stringify(payload) });
        showToast('Created');
        hideModal();
        await loadTabData();
        renderTable();
        await loadStats();
      } catch (e) {
        showToast(e.message);
      }
    });
    Object.keys(base).forEach((k) => {
      if (k === 'location' || k === 'asset_location') setOfficeSelectValue(`nc_${k}`, base[k]);
    });
  }

  function openAddAsset() {
    if (state.tab === 'gatepass') {
      openGatepassModal(null);
      return;
    }
    if (state.tab === 'leavers') {
      openLeaverModal(null);
      return;
    }
    if (state.tab === 'audit') {
      showToast('Audit log is read-only');
      return;
    }
    if (state.tab === 'employee') {
      const map = { laptop: 'laptops', desktop: 'desktops', monitor: 'monitors', accessory: 'accessories' };
      const tbl = map[state.empChip];
      if (!tbl) {
        showToast('Choose Laptop, Desktop, Monitor, or Accessories chip first');
        return;
      }
      openSimpleCreate(tbl, {});
      return;
    }
    if (state.tab === 'admin') {
      const map = { ups: 'ups', mobile: 'mobile_phones', scanner: 'scanners_printers', camera: 'cameras_dvr' };
      const tbl = map[state.admChip];
      if (!tbl) {
        showToast('Choose a device type chip first');
        return;
      }
      openSimpleCreate(tbl, {});
      return;
    }
    const m = { networking: 'networking', cloud: 'cloud_assets', infodesk: 'infodesk_applications', third_party: 'third_party_software' };
    const tbl = m[state.tab];
    if (tbl) openSimpleCreate(tbl, {});
  }

  async function switchTab(tab) {
    state.tab = tab;
    $$('#main-tabs .tab').forEach((b) => b.classList.toggle('active', b.dataset.tab === tab));
    $('#chips-employee').hidden = tab !== 'employee';
    $('#chips-admin').hidden = tab !== 'admin';
    setFiltersVisible(tab !== 'audit');
    updateToolbar();
    try {
      await loadTabData();
      renderTable();
    } catch (e) {
      showToast(e.message);
    }
    await loadStats();
  }

  function wireFilters() {
    ['f-search', 'f-status', 'f-dept', 'f-location', 'f-pii', 'f-iso'].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.addEventListener('input', () => renderTable());
      if (el) el.addEventListener('change', () => renderTable());
    });
  }

  async function init() {
    $('#btn-export-all').addEventListener('click', () => { window.location.href = '/api/export/all'; });
    $('#btn-add-asset').addEventListener('click', () => openAddAsset());
    $('#main-tabs').addEventListener('click', (e) => {
      const b = e.target.closest('.tab');
      if (!b || !b.dataset.tab) return;
      switchTab(b.dataset.tab);
    });
    $$('[data-emp-chip]').forEach((b) => {
      b.addEventListener('click', () => {
        $$('[data-emp-chip]').forEach((x) => x.classList.remove('active'));
        b.classList.add('active');
        state.empChip = b.dataset.empChip;
        renderTable();
      });
    });
    $$('[data-adm-chip]').forEach((b) => {
      b.addEventListener('click', () => {
        $$('[data-adm-chip]').forEach((x) => x.classList.remove('active'));
        b.classList.add('active');
        state.admChip = b.dataset.admChip;
        renderTable();
      });
    });
    $('#modal-close').addEventListener('click', hideModal);
    $('#modal-cancel').addEventListener('click', hideModal);
    $('#modal-save').addEventListener('click', () => {
      if (typeof state._modalSave === 'function') state._modalSave();
    });
    $('#panel-close').addEventListener('click', hidePanel);
    $('#audit-prev').addEventListener('click', async () => {
      if (state.auditPage > 1) {
        state.auditPage -= 1;
        await loadAuditPage();
      }
    });
    $('#audit-next').addEventListener('click', async () => {
      if (state.auditPage * 50 < state.auditTotal) {
        state.auditPage += 1;
        await loadAuditPage();
      }
    });
    wireFilters();
    wireTableBody();
    await loadStats();
    await switchTab('employee');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
