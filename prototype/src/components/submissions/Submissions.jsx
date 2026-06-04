import React, { useState, useEffect, useCallback } from 'react';
import { C } from '../../tokens.js';
import { submissionsApi, usesDemoData } from '../../api/client.js';

// ── Demo data ─────────────────────────────────────────────────────────────────
const DEMO = [
  { id: '1', org_name: 'Plan International SL',       period: 'Mar–Apr 2026', status: 'verified',  submitted_at: '2026-04-12', verified_at: '2026-04-20', key_results: 'Reached 3,240 beneficiaries across 5 schools.', expenditure: 42000, expenditure_currency: 'USD', budget_util: 'On track',    safeguarding_cases: true,  cases_reported: 3, cases_referred: 2, challenges: 'Access constraints in remote communities.', focus_areas: ['SRGBV Prevention & Response', 'MHPSS'] },
  { id: '2', org_name: 'UNICEF Sierra Leone',          period: 'Mar–Apr 2026', status: 'verified',  submitted_at: '2026-04-09', verified_at: '2026-04-18', key_results: 'Reached 5,180 beneficiaries across 8 schools.', expenditure: 98000, expenditure_currency: 'USD', budget_util: 'On track',    safeguarding_cases: false, cases_reported: 0, cases_referred: 0, challenges: null,                                               focus_areas: ['School Governance', 'WASH'] },
  { id: '3', org_name: 'World Vision SL',              period: 'Mar–Apr 2026', status: 'submitted', submitted_at: '2026-04-14', verified_at: null,          key_results: 'Reached 1,870 beneficiaries across 4 schools.', expenditure: 27500, expenditure_currency: 'USD', budget_util: 'Under-spending', safeguarding_cases: true,  cases_reported: 1, cases_referred: 1, challenges: 'Staff turnover delayed activities.',        focus_areas: ['Life Skills / SRH'] },
  { id: '4', org_name: 'IRC Sierra Leone',             period: 'Mar–Apr 2026', status: 'verified',  submitted_at: '2026-04-07', verified_at: '2026-04-15', key_results: 'Reached 4,020 beneficiaries across 6 schools.', expenditure: 61000, expenditure_currency: 'USD', budget_util: 'On track',    safeguarding_cases: false, cases_reported: 0, cases_referred: 0, challenges: null,                                               focus_areas: ['SRGBV Prevention & Response', 'Social Protection'] },
  { id: '5', org_name: 'Catholic Relief Services',    period: 'Mar–Apr 2026', status: 'submitted', submitted_at: '2026-04-18', verified_at: null,          key_results: 'Reached 980 beneficiaries across 2 schools.',  expenditure: 15000, expenditure_currency: 'USD', budget_util: 'On track',    safeguarding_cases: false, cases_reported: 0, cases_referred: 0, challenges: 'Rainy season disrupted field visits.',        focus_areas: ['WASH'] },
  { id: '6', org_name: 'Concern Worldwide SL',        period: 'Mar–Apr 2026', status: 'verified',  submitted_at: '2026-04-11', verified_at: '2026-04-19', key_results: 'Reached 2,100 beneficiaries across 3 schools.', expenditure: 33000, expenditure_currency: 'USD', budget_util: 'On track',    safeguarding_cases: true,  cases_reported: 2, cases_referred: 2, challenges: null,                                               focus_areas: ['MHPSS', 'Social Norms'] },
  { id: '7', org_name: 'Save the Children SL',        period: 'Mar–Apr 2026', status: 'verified',  submitted_at: '2026-04-10', verified_at: '2026-04-17', key_results: 'Reached 6,340 beneficiaries across 9 schools.', expenditure: 112000, expenditure_currency: 'USD', budget_util: 'On track',   safeguarding_cases: true,  cases_reported: 4, cases_referred: 3, challenges: null,                                               focus_areas: ['SRGBV Prevention & Response', 'MHPSS', 'Life Skills / SRH'] },
  { id: '8', org_name: 'Girl Child Network SL',       period: 'Mar–Apr 2026', status: 'draft',     submitted_at: null,         verified_at: null,          key_results: null,                                           expenditure: null, expenditure_currency: 'USD', budget_util: null,           safeguarding_cases: false, cases_reported: 0, cases_referred: 0, challenges: null,                                               focus_areas: [] },
];

// ── Helpers ──────────────────────────────────────────────────────────────────
const STATUS = {
  verified:  { label: 'Verified',  bg: '#f0fdf4', color: '#15803d', border: '#bbf7d0' },
  submitted: { label: 'Submitted', bg: '#fffbeb', color: '#b45309', border: '#fde68a' },
  draft:     { label: 'Draft',     bg: '#f8fafc', color: '#64748b', border: '#e2e8f0' },
};

function Badge({ status }) {
  const s = STATUS[status] ?? STATUS.draft;
  return (
    <span style={{
      fontSize: 10, fontWeight: 600, padding: '2px 8px', borderRadius: 10,
      background: s.bg, color: s.color, border: `1px solid ${s.border}`,
    }}>{s.label}</span>
  );
}

function fmt(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

function DetailPanel({ sub, loading, isAdmin, onVerify, onClose }) {
  const [verifying, setVerifying] = useState(false);

  async function handleVerify() {
    setVerifying(true);
    await onVerify(sub.id);
    setVerifying(false);
  }

  const money = sub.expenditure != null
    ? `${sub.expenditure_currency || 'USD'} ${Number(sub.expenditure).toLocaleString()}`
    : '—';
  const activities = sub.activities ?? [];
  const locations  = sub.locations ?? [];

  return (
    <div style={{
      background: C.bg, border: `1px solid ${C.border}`, borderRadius: 6,
      padding: '16px 20px', margin: '0 0 2px 0',
    }}>
      {/* Header row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
        <div>
          <div style={{ fontWeight: 600, fontSize: 13 }}>{sub.org_name}</div>
          <div style={{ fontSize: 11, color: C.textSec, marginTop: 2 }}>{sub.period} · <Badge status={sub.status} /></div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {isAdmin && sub.status === 'submitted' && (
            <button onClick={handleVerify} disabled={verifying} style={{
              fontSize: 11, padding: '5px 14px', borderRadius: 4, cursor: 'pointer',
              background: C.blue600, color: C.white, border: 'none', fontWeight: 600,
            }}>{verifying ? 'Verifying…' : '✓ Verify'}</button>
          )}
          <button onClick={onClose} style={{
            fontSize: 11, padding: '5px 10px', borderRadius: 4, cursor: 'pointer',
            background: 'transparent', color: C.textSec, border: `1px solid ${C.border}`,
          }}>Close</button>
        </div>
      </div>

      {loading ? (
        <div style={{ fontSize: 12, color: C.textSec, padding: '12px 0' }}>Loading report details…</div>
      ) : sub._error ? (
        <div style={{ fontSize: 12, color: C.red700, padding: '12px 0' }}>⚠ Could not load details: {sub._error}</div>
      ) : (
      <>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 32px' }}>
        {/* Left column — narrative */}
        <div>
          <Section title="Results & outcomes" />
          <Field label="Key results" value={sub.key_results} />
          <Field label="Observed changes" value={sub.observed_changes} />
          <Field label="Early outcomes" value={sub.early_outcomes} />

          <Section title="Challenges & risks" />
          <Field label="Challenges" value={sub.challenges} />
          <Field label="Risks" value={sub.risks} />
          <Field label="Mitigations" value={sub.mitigations} />

          <Section title="Looking ahead" />
          <Field label="Planned activities" value={sub.planned_activities} />
          <Field label="Support needed" value={sub.support_needed} />
        </div>

        {/* Right column — quantitative + coordination + safeguarding */}
        <div>
          <Section title="Status & finance" />
          <Row label="Submitted"       value={fmt(sub.submitted_at)} />
          <Row label="Verified"        value={fmt(sub.verified_at)} />
          <Row label="Expenditure"     value={money} />
          <Row label="Budget util."    value={sub.budget_util ?? '—'} />

          <Section title="Coordination" />
          <Row label="Gov. engaged"    value={sub.gov_engaged ? 'Yes' : 'No'} />
          {sub.gov_engaged_list && <Row label="Counterparts" value={sub.gov_engaged_list} />}
          <Row label="Coord. meetings" value={sub.coordination_meetings ?? 0} />
          {sub.key_partners && <Row label="Key partners" value={sub.key_partners} />}

          <Section title="Safeguarding" />
          <Row label="Cases reported"  value={sub.cases_reported ?? 0} />
          <Row label="Cases referred"  value={sub.cases_referred ?? 0} />
          {sub.referral_pathway && <Row label="Referral pathway" value={sub.referral_pathway} />}
          {sub.safeguarding_action && <Field label="Action taken" value={sub.safeguarding_action} />}

          {(sub.focus_areas ?? []).length > 0 && (
            <div style={{ marginTop: 12 }}>
              <div style={{ fontSize: 10, color: C.textMuted, marginBottom: 4 }}>FOCUS AREAS</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {sub.focus_areas.map(fa => (
                  <span key={fa} style={{ fontSize: 10, padding: '2px 7px', borderRadius: 10, background: C.blueBg, color: C.blue600, border: `1px solid ${C.blue100}` }}>{fa}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Activities — full width */}
      {activities.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <Section title={`Activities (${activities.length})`} />
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1.2fr 1fr 90px 90px 70px', gap: '0', fontSize: 10, fontWeight: 600, color: C.textMuted, textTransform: 'uppercase', letterSpacing: '.04em', padding: '4px 8px', background: C.borderLight, borderRadius: 4 }}>
            <div>Activity</div><div>Type</div><div>Status</div><div>Students F/M</div><div>Teachers F/M</div><div>Schools</div>
          </div>
          {activities.map((a, i) => (
            <div key={i} style={{ display: 'grid', gridTemplateColumns: '2fr 1.2fr 1fr 90px 90px 70px', gap: '0', fontSize: 11, padding: '6px 8px', borderBottom: `1px solid ${C.borderLight}`, alignItems: 'center' }}>
              <div style={{ fontWeight: 500 }}>{a.activity_title || '—'}</div>
              <div style={{ color: C.textSec }}>{a.activity_type || '—'}</div>
              <div style={{ color: C.textSec }}>{a.implementation_status || '—'}</div>
              <div>{(a.students_f ?? 0).toLocaleString()} / {(a.students_m ?? 0).toLocaleString()}</div>
              <div>{(a.teachers_f ?? 0)} / {(a.teachers_m ?? 0)}</div>
              <div>{a.schools_total ?? 0}</div>
            </div>
          ))}
        </div>
      )}

      {/* Locations */}
      {locations.length > 0 && (
        <div style={{ marginTop: 14 }}>
          <Section title="Locations" />
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {locations.map((l, i) => (
              <span key={i} style={{ fontSize: 10, padding: '3px 8px', borderRadius: 4, background: C.white, border: `1px solid ${C.border}`, color: C.textSec }}>
                {[l.district_name, l.chiefdom_name, l.community_name, l.school_name].filter(Boolean).join(' · ') || '—'}
              </span>
            ))}
          </div>
        </div>
      )}
      </>
      )}
    </div>
  );
}

function Section({ title }) {
  return (
    <div style={{ fontSize: 10, fontWeight: 700, color: C.blue600, textTransform: 'uppercase', letterSpacing: '.06em', margin: '12px 0 6px', borderBottom: `1px solid ${C.border}`, paddingBottom: 3 }}>
      {title}
    </div>
  );
}

function Field({ label, value }) {
  if (!value) return null;
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ fontSize: 10, color: C.textMuted, textTransform: 'uppercase', letterSpacing: '.05em', marginBottom: 2 }}>{label}</div>
      <div style={{ fontSize: 12, color: C.text }}>{value}</div>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: `1px solid ${C.borderLight}`, fontSize: 12, gap: 12 }}>
      <span style={{ color: C.textSec, flexShrink: 0 }}>{label}</span>
      <span style={{ fontWeight: 500, textAlign: 'right' }}>{String(value)}</span>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function Submissions({ user }) {
  const isAdmin  = user?.role === 'admin';
  const isViewer = user?.role === 'viewer';

  const [rows, setRows]         = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);
  const [search, setSearch]     = useState('');
  const [statusF, setStatusF]   = useState('all');
  const [expanded, setExpanded] = useState(null);
  const [detail, setDetail]         = useState(null);   // full detail for expanded row
  const [detailLoading, setDetailLoading] = useState(false);

  async function toggleExpand(row) {
    if (expanded === row.id) { setExpanded(null); setDetail(null); return; }
    setExpanded(row.id);
    setDetail(null);
    if (usesDemoData()) { setDetail(row); return; }  // demo rows already carry detail
    setDetailLoading(true);
    try {
      const full = await submissionsApi.get(row.id);
      setDetail({ ...full, period: full.period_label ?? full.period ?? row.period });
    } catch (e) {
      setDetail({ ...row, _error: e.message });
    } finally {
      setDetailLoading(false);
    }
  }

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (usesDemoData()) {
        setRows(DEMO);
      } else {
        const params = {};
        if (statusF !== 'all') params.status_filter = statusF;
        const data = await submissionsApi.list(params);
        // Normalise API shape → UI shape (period_label → period)
        setRows(data.map(r => ({ ...r, period: r.period_label ?? r.period ?? '—' })));
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [statusF]);

  useEffect(() => { load(); }, [load]);

  async function handleVerify(id) {
    if (!usesDemoData()) {
      await submissionsApi.adminPatch(id, { status: 'verified' });
    }
    setRows(prev => prev.map(r => r.id === id ? { ...r, status: 'verified', verified_at: new Date().toISOString() } : r));
    setExpanded(null);
    setDetail(null);
  }

  const filtered = rows.filter(r => {
    const q = search.toLowerCase();
    const matchSearch = !q || (r.org_name ?? '').toLowerCase().includes(q);
    const matchStatus = statusF === 'all' || r.status === statusF;
    return matchSearch && matchStatus;
  });

  const counts = {
    all: rows.length,
    verified:  rows.filter(r => r.status === 'verified').length,
    submitted: rows.filter(r => r.status === 'submitted').length,
    draft:     rows.filter(r => r.status === 'draft').length,
  };

  return (
    <main style={{ flex: 1, padding: '18px 24px', overflow: 'auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 3 }}>Submissions</div>
          <div style={{ fontSize: 11, color: C.textSec }}>
            Partner activity reports — review, verify and track submission status
          </div>
        </div>
        <div style={{ fontSize: 11, color: C.textSec }}>{filtered.length} of {rows.length} submissions</div>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 16, alignItems: 'center' }}>
        <input
          placeholder="Search by partner…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{
            fontSize: 12, padding: '6px 10px', border: `1px solid ${C.border}`,
            borderRadius: 4, width: 220, outline: 'none',
          }}
        />
        <div style={{ display: 'flex', gap: 1, background: C.borderLight, borderRadius: 5, padding: 2 }}>
          {['all', 'verified', 'submitted', 'draft'].map(s => (
            <button key={s} onClick={() => setStatusF(s)} style={{
              fontSize: 11, padding: '4px 10px', borderRadius: 4, border: 'none', cursor: 'pointer',
              background: statusF === s ? C.white : 'transparent',
              color: statusF === s ? C.text : C.textSec,
              fontWeight: statusF === s ? 600 : 400,
              boxShadow: statusF === s ? '0 1px 2px rgba(0,0,0,.08)' : 'none',
            }}>
              {s === 'all' ? 'All' : STATUS[s].label} <span style={{ color: C.textMuted }}>({counts[s]})</span>
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div style={{ color: C.textSec, fontSize: 12, padding: 24 }}>Loading…</div>
      ) : error ? (
        <div style={{ color: C.red500, fontSize: 12, padding: 24 }}>{error}</div>
      ) : (
        <div style={{ background: C.white, border: `1px solid ${C.border}`, borderRadius: 6, overflow: 'hidden' }}>
          {/* Table header */}
          <div style={{
            display: 'grid', gridTemplateColumns: '2fr 1fr 100px 120px 120px 80px',
            padding: '8px 16px', background: C.bg, borderBottom: `1px solid ${C.border}`,
            fontSize: 10, fontWeight: 600, color: C.textMuted, textTransform: 'uppercase', letterSpacing: '.05em',
          }}>
            <div>Partner</div><div>Period</div><div>Status</div>
            <div>Submitted</div><div>Verified</div><div></div>
          </div>

          {filtered.length === 0 && (
            <div style={{ padding: 24, textAlign: 'center', color: C.textSec, fontSize: 12 }}>
              No submissions match the current filters.
            </div>
          )}

          {filtered.map(row => (
            <React.Fragment key={row.id}>
              <div
                onClick={() => toggleExpand(row)}
                style={{
                  display: 'grid', gridTemplateColumns: '2fr 1fr 100px 120px 120px 80px',
                  padding: '10px 16px', borderBottom: `1px solid ${C.borderLight}`,
                  cursor: 'pointer', alignItems: 'center',
                  background: expanded === row.id ? C.blueBg : 'transparent',
                  transition: 'background .1s',
                }}
              >
                <div style={{ fontSize: 12, fontWeight: 500 }}>{row.org_name}</div>
                <div style={{ fontSize: 11, color: C.textSec }}>{row.period}</div>
                <div><Badge status={row.status} /></div>
                <div style={{ fontSize: 11, color: C.textSec }}>{fmt(row.submitted_at)}</div>
                <div style={{ fontSize: 11, color: C.textSec }}>{fmt(row.verified_at)}</div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ fontSize: 10, color: C.blue600 }}>
                    {expanded === row.id ? '▲ Close' : '▼ View'}
                  </span>
                </div>
              </div>

              {expanded === row.id && (
                <DetailPanel
                  sub={detail ?? row}
                  loading={detailLoading}
                  isAdmin={isAdmin}
                  onVerify={handleVerify}
                  onClose={() => { setExpanded(null); setDetail(null); }}
                />
              )}
            </React.Fragment>
          ))}
        </div>
      )}
    </main>
  );
}
