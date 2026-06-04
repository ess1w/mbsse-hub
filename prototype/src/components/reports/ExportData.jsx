import React, { useState } from 'react';
import { C } from '../../tokens.js';
import { submissionsApi, usesDemoData } from '../../api/client.js';

const PERIODS  = ['Mar–Apr 2026', 'Jan–Feb 2026', 'Nov–Dec 2025'];
const STATUSES = ['All', 'Verified', 'Submitted', 'Draft'];
const DISTRICTS = [
  'All districts', 'Bo', 'Bombali', 'Bonthe', 'Falaba', 'Kailahun', 'Kambia',
  'Karene', 'Kenema', 'Koinadugu', 'Kono', 'Moyamba',
  'Port Loko', 'Pujehun', 'Tonkolili', 'Western Area Rural', 'Western Area Urban',
];

// Fields included in the CSV export
const EXPORT_FIELDS = [
  { key: 'org_name',              label: 'Organisation' },
  { key: 'period',                label: 'Reporting Period' },
  { key: 'status',                label: 'Status' },
  { key: 'submitted_at',          label: 'Submitted Date' },
  { key: 'verified_at',           label: 'Verified Date' },
  { key: 'key_results',           label: 'Key Results' },
  { key: 'observed_changes',      label: 'Observed Changes' },
  { key: 'early_outcomes',        label: 'Early Outcomes' },
  { key: 'expenditure',           label: 'Expenditure' },
  { key: 'expenditure_currency',  label: 'Currency' },
  { key: 'budget_util',           label: 'Budget Utilisation' },
  { key: 'gov_engaged',           label: 'Government Engaged' },
  { key: 'coordination_meetings', label: 'Coordination Meetings' },
  { key: 'safeguarding_cases',    label: 'Safeguarding Cases' },
  { key: 'cases_reported',        label: 'Cases Reported' },
  { key: 'cases_referred',        label: 'Cases Referred' },
  { key: 'challenges',            label: 'Challenges' },
  { key: 'planned_activities',    label: 'Planned Activities' },
];

function escapeCSV(val) {
  if (val == null) return '';
  const str = String(val);
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

function buildCSV(rows) {
  const header = EXPORT_FIELDS.map(f => f.label).join(',');
  const body = rows.map(r =>
    EXPORT_FIELDS.map(f => escapeCSV(r[f.key])).join(',')
  ).join('\n');
  return `${header}\n${body}`;
}

function downloadCSV(content, filename) {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function ExportData() {
  const [period,   setPeriod]   = useState(PERIODS[0]);
  const [status,   setStatus]   = useState('All');
  const [district, setDistrict] = useState('All districts');
  const [loading,  setLoading]  = useState(false);
  const [lastExport, setLastExport] = useState(null);

  async function handleExport() {
    setLoading(true);
    try {
      let rows;
      if (usesDemoData()) {
        // Use a small representative set in demo mode
        rows = [
          { org_name: 'Plan International SL', period, status: 'verified', submitted_at: '2026-04-12', verified_at: '2026-04-20', key_results: 'Reached 3,240 beneficiaries.', observed_changes: 'Improved awareness.', early_outcomes: 'Increased referrals.', expenditure: 42000, expenditure_currency: 'USD', budget_util: 'On track', gov_engaged: true, coordination_meetings: 3, safeguarding_cases: true, cases_reported: 3, cases_referred: 2, challenges: null, planned_activities: 'Continue school sessions.' },
          { org_name: 'UNICEF Sierra Leone',    period, status: 'verified', submitted_at: '2026-04-09', verified_at: '2026-04-18', key_results: 'Reached 5,180 beneficiaries.', observed_changes: 'Better reporting.', early_outcomes: 'Policy uptake.', expenditure: 98000, expenditure_currency: 'USD', budget_util: 'On track', gov_engaged: true, coordination_meetings: 5, safeguarding_cases: false, cases_reported: 0, cases_referred: 0, challenges: null, planned_activities: 'Scale to new schools.' },
        ];
      } else {
        const params = {};
        if (status !== 'All') params.status_filter = status.toLowerCase();
        const data = await submissionsApi.list(params);
        // Normalise API shape → export shape (period_label → period)
        rows = data.map(r => ({ ...r, period: r.period_label ?? r.period ?? '' }));
      }

      // Apply district filter client-side (organisations have a districts array)
      if (district !== 'All districts') {
        rows = rows.filter(r =>
          Array.isArray(r.districts)
            ? r.districts.includes(district)
            : true
        );
      }

      const timestamp = new Date().toISOString().slice(0, 10);
      const filename  = `mbsse_submissions_${period.replace(/[^a-z0-9]/gi, '_')}_${timestamp}.csv`;
      const csv       = buildCSV(rows);
      downloadCSV(csv, filename);
      setLastExport({ filename, count: rows.length, at: new Date().toLocaleTimeString() });
    } catch (e) {
      alert(`Export failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ flex: 1, padding: '18px 24px', overflow: 'auto' }}>
      <div style={{ maxWidth: 560 }}>
        {/* Header */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 3 }}>Export Data</div>
          <div style={{ fontSize: 11, color: C.textSec }}>
            Download submission data as a CSV file. Apply filters to narrow the export.
          </div>
        </div>

        {/* Filter card */}
        <div style={{
          background: C.white, border: `1px solid ${C.border}`,
          borderRadius: 6, padding: '20px 24px', marginBottom: 16,
        }}>
          <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 16 }}>Export filters</div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
            <Label text="Reporting period">
              <Select value={period} onChange={setPeriod} options={PERIODS} />
            </Label>
            <Label text="Status">
              <Select value={status} onChange={setStatus} options={STATUSES} />
            </Label>
            <Label text="District">
              <Select value={district} onChange={setDistrict} options={DISTRICTS} />
            </Label>
          </div>

          {/* Fields included */}
          <div style={{ fontSize: 11, color: C.textSec, marginBottom: 16 }}>
            <span style={{ fontWeight: 500 }}>Fields included:</span>{' '}
            {EXPORT_FIELDS.map(f => f.label).join(', ')}
          </div>

          <button
            onClick={handleExport}
            disabled={loading}
            style={{
              width: '100%', padding: '9px 0', fontSize: 13, fontWeight: 600,
              background: C.blue600, color: C.white, border: 'none',
              borderRadius: 4, cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? 'Preparing export…' : '⬇ Download CSV'}
          </button>
        </div>

        {/* Last export confirmation */}
        {lastExport && (
          <div style={{
            background: '#f0fdf4', border: '1px solid #bbf7d0',
            borderRadius: 6, padding: '12px 16px', fontSize: 12, color: '#15803d',
          }}>
            ✓ <strong>{lastExport.filename}</strong> downloaded — {lastExport.count} submission{lastExport.count !== 1 ? 's' : ''} at {lastExport.at}
          </div>
        )}

        {/* Note about Excel */}
        <div style={{
          marginTop: 16, padding: '12px 16px', background: C.bg,
          border: `1px solid ${C.border}`, borderRadius: 6, fontSize: 11, color: C.textSec,
        }}>
          <strong style={{ color: C.text }}>Need Excel format?</strong> Open the downloaded CSV in Excel or Google Sheets —
          both import CSV files directly without any conversion needed.
        </div>
      </div>
    </main>
  );
}

function Label({ text, children }) {
  return (
    <div>
      <div style={{ fontSize: 11, fontWeight: 500, color: C.textSec, marginBottom: 5 }}>{text}</div>
      {children}
    </div>
  );
}

function Select({ value, onChange, options }) {
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      style={{
        width: '100%', fontSize: 12, padding: '6px 8px',
        border: `1px solid ${C.border}`, borderRadius: 4,
        background: C.white, color: C.text, outline: 'none',
      }}
    >
      {options.map(o => <option key={o} value={o}>{o}</option>)}
    </select>
  );
}
