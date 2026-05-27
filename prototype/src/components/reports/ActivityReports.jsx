import React from 'react';
import { C } from '../../tokens.js';

const MOCK_REPORTS = [
  { org: 'Plan International Sierra Leone', period: 'Mar–Apr 2026', submitted: '12 Apr 2026', status: 'Verified',   activities: 4, beneficiaries: 3240 },
  { org: 'UNICEF Sierra Leone',             period: 'Mar–Apr 2026', submitted: '9 Apr 2026',  status: 'Verified',   activities: 6, beneficiaries: 5180 },
  { org: 'World Vision SL',                 period: 'Mar–Apr 2026', submitted: '14 Apr 2026', status: 'Pending',    activities: 3, beneficiaries: 1870 },
  { org: 'IRC Sierra Leone',                period: 'Mar–Apr 2026', submitted: '7 Apr 2026',  status: 'Verified',   activities: 5, beneficiaries: 4020 },
  { org: 'Catholic Relief Services',        period: 'Mar–Apr 2026', submitted: '18 Apr 2026', status: 'Pending',    activities: 2, beneficiaries: 980  },
  { org: 'Concern Worldwide SL',            period: 'Mar–Apr 2026', submitted: '11 Apr 2026', status: 'Verified',   activities: 3, beneficiaries: 2100 },
  { org: 'Save the Children SL',            period: 'Mar–Apr 2026', submitted: '10 Apr 2026', status: 'Verified',   activities: 7, beneficiaries: 6340 },
  { org: 'Girl Child Network SL',           period: 'Mar–Apr 2026', submitted: null,           status: 'Draft',      activities: 1, beneficiaries: 0    },
];

const STATUS_STYLE = {
  Verified: { bg: '#f0fdf4', color: '#15803d', border: '#bbf7d0' },
  Pending:  { bg: '#fffbeb', color: '#b45309', border: '#fde68a' },
  Draft:    { bg: '#f8fafc', color: '#64748b', border: '#e2e8f0' },
};

export default function ActivityReports({ user }) {
  const [search, setSearch] = React.useState('');
  const [statusFilter, setStatusFilter] = React.useState('All');

  const filtered = MOCK_REPORTS.filter(r => {
    const matchSearch = r.org.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === 'All' || r.status === statusFilter;
    return matchSearch && matchStatus;
  });

  return (
    <main style={{ flex: 1, padding: '18px 20px', overflow: 'auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 3 }}>Activity Reports</div>
        <div style={{ fontSize: 11, color: C.textSec }}>
          Summary of submitted partner activity reports — Mar–Apr 2026 cycle
        </div>
      </div>

      {/* Coming-soon notice */}
      <div style={{
        background: C.blueBg, border: `1px solid ${C.blue100}`, borderRadius: 8,
        padding: '12px 16px', marginBottom: 16, display: 'flex', alignItems: 'flex-start', gap: 10,
      }}>
        <span style={{ fontSize: 16, flexShrink: 0 }}>ℹ</span>
        <div style={{ fontSize: 11, color: C.blue900, lineHeight: 1.6 }}>
          <strong>Full report view coming soon.</strong> When the backend is connected this page will list
          all submitted activity reports with drill-down into each submission, inline verification controls
          for admins, and export to CSV / Excel. The data below is illustrative.
        </div>
      </div>

      {/* Filters */}
      <div style={{
        background: C.white, border: `1px solid ${C.border}`, borderRadius: 8,
        padding: '10px 14px', marginBottom: 14, display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap',
      }}>
        <span style={{ fontSize: 11, fontWeight: 600, color: C.textSec }}>Filter:</span>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search organisation…"
          style={{ fontSize: 11, padding: '5px 10px', border: `1px solid ${C.border}`, borderRadius: 5, width: 200, outline: 'none' }}
        />
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          style={{ fontSize: 11, padding: '5px 9px', border: `1px solid ${C.border}`, borderRadius: 5, background: C.white }}
        >
          {['All', 'Verified', 'Pending', 'Draft'].map(s => <option key={s}>{s}</option>)}
        </select>
        <select style={{ fontSize: 11, padding: '5px 9px', border: `1px solid ${C.border}`, borderRadius: 5, background: C.white }}>
          <option>Mar–Apr 2026</option>
          <option>Jan–Feb 2026</option>
          <option>Nov–Dec 2025</option>
        </select>
        <span style={{ marginLeft: 'auto', fontSize: 11, color: C.textMuted }}>
          {filtered.length} of {MOCK_REPORTS.length} reports
        </span>
      </div>

      {/* Table */}
      <div style={{ background: C.white, border: `1px solid ${C.border}`, borderRadius: 8, overflow: 'hidden' }}>
        {/* Table header */}
        <div style={{
          display: 'grid', gridTemplateColumns: '2.5fr 1fr 1fr 0.7fr 1fr 0.8fr',
          padding: '9px 16px', background: '#f8fafc', borderBottom: `1px solid ${C.border}`,
          fontSize: 10, fontWeight: 600, color: C.textMuted, textTransform: 'uppercase', letterSpacing: '.05em',
        }}>
          <span>Organisation</span>
          <span>Period</span>
          <span>Submitted</span>
          <span>Activities</span>
          <span>Beneficiaries</span>
          <span>Status</span>
        </div>

        {filtered.length === 0 && (
          <div style={{ padding: '32px 16px', textAlign: 'center', fontSize: 12, color: C.textMuted }}>
            No reports match the current filters.
          </div>
        )}

        {filtered.map((r, i) => {
          const s = STATUS_STYLE[r.status];
          return (
            <div key={r.org} style={{
              display: 'grid', gridTemplateColumns: '2.5fr 1fr 1fr 0.7fr 1fr 0.8fr',
              padding: '11px 16px', fontSize: 11,
              borderBottom: i < filtered.length - 1 ? `1px solid ${C.borderLight}` : 'none',
              alignItems: 'center',
            }}>
              <span style={{ fontWeight: 500, color: C.text }}>{r.org}</span>
              <span style={{ color: C.textSec }}>{r.period}</span>
              <span style={{ color: r.submitted ? C.textSec : C.textMuted }}>
                {r.submitted ?? '—'}
              </span>
              <span style={{ color: C.textSec }}>{r.activities}</span>
              <span style={{ color: C.textSec }}>
                {r.beneficiaries > 0 ? r.beneficiaries.toLocaleString() : '—'}
              </span>
              <span style={{
                display: 'inline-flex', alignItems: 'center', padding: '2px 8px',
                borderRadius: 10, fontSize: 10, fontWeight: 500,
                background: s.bg, color: s.color, border: `1px solid ${s.border}`,
              }}>
                {r.status}
              </span>
            </div>
          );
        })}
      </div>

      {/* Footer note */}
      <div style={{ marginTop: 12, fontSize: 10, color: C.textMuted, textAlign: 'right', fontStyle: 'italic' }}>
        Prototype v1.0 — illustrative data only · MBSSE School Safety Coordination Hub · May 2026
      </div>
    </main>
  );
}
