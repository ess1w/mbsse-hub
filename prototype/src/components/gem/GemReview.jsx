import React, { useState, useEffect, useMemo } from 'react';
import { C } from '../../tokens.js';
import { gemReportsApi } from '../../api/gemReportsApi.js';

const STATUS = {
  submitted: { bg: C.amberBg, color: C.amber700, label: 'Awaiting review' },
  reviewed:  { bg: C.greenBg, color: C.green,    label: 'Reviewed' },
  draft:     { bg: C.borderLight, color: C.textMuted, label: 'Draft' },
};

function Badge({ status }) {
  const s = STATUS[status] ?? STATUS.draft;
  return <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 10, background: s.bg, color: s.color, fontWeight: 600 }}>{s.label}</span>;
}

const fmtMonth = (d) => d ? new Date(d).toLocaleDateString(undefined, { month: 'long', year: 'numeric' }) : '—';

function Detail({ report, onReview, onClose, canReview }) {
  const [busy, setBusy] = useState(false);
  const num = (label, val) => (
    <div style={{ fontSize: 11 }}>
      <div style={{ color: C.textMuted, fontSize: 10 }}>{label}</div>
      <div style={{ color: C.text, fontWeight: 600, marginTop: 1 }}>{(val ?? 0).toLocaleString()}</div>
    </div>
  );
  return (
    <div style={{ background: C.bg, border: `1px solid ${C.border}`, borderRadius: 6, padding: '16px 20px', margin: '0 0 2px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
        <div>
          <div style={{ fontWeight: 600, fontSize: 13 }}>{report.coordinator_name} — {report.district_name}</div>
          <div style={{ fontSize: 11, color: C.textSec, marginTop: 2 }}>{fmtMonth(report.reporting_month)} · <Badge status={report.status} /></div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {canReview && report.status === 'submitted' && (
            <button disabled={busy} onClick={async () => { setBusy(true); await onReview(report.id); setBusy(false); }}
              style={{ fontSize: 11, padding: '5px 14px', borderRadius: 4, cursor: 'pointer', background: C.blue600, color: C.white, border: 'none', fontWeight: 600 }}>
              {busy ? 'Saving…' : '✓ Mark reviewed'}
            </button>
          )}
          <button onClick={onClose} style={{ fontSize: 11, padding: '5px 10px', borderRadius: 4, cursor: 'pointer', background: 'transparent', color: C.textSec, border: `1px solid ${C.border}` }}>Close</button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 14 }}>
        {num('Schools covered', report.schools_covered)}
        {num('Activities', report.total_activities)}
        {num('Participants', report.total_participants)}
        {num('Functional clubs', report.functional_clubs)}
        {num('Girls reached', report.girls_reached)}
        {num('Boys reached', report.boys_reached)}
        {num('Teenage girls', report.teenage_girls)}
        {num('Children w/ disability', report.children_disability)}
        {num('Teachers/parents/community', report.teachers_parents_community)}
        {num('SRGBV referrals', report.srgbv_referrals)}
      </div>

      <div style={{ fontSize: 11, marginBottom: 8 }}>
        <div style={{ color: C.textMuted, fontSize: 10 }}>Implementation status</div>
        <div style={{ color: C.text, marginTop: 1 }}>{report.impl_status}{report.impl_reason ? ` — ${report.impl_reason}` : ''}{report.impl_reason_other ? ` (${report.impl_reason_other})` : ''}</div>
      </div>
      {(report.activities_conducted ?? []).length > 0 && (
        <div style={{ fontSize: 11, marginBottom: 8 }}>
          <div style={{ color: C.textMuted, fontSize: 10, marginBottom: 3 }}>Activities conducted</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {report.activities_conducted.map(a => <span key={a} style={{ fontSize: 10, padding: '2px 7px', borderRadius: 10, background: C.blueBg, color: C.blue600, border: `1px solid ${C.blue100}` }}>{a === 'Other' && report.activity_other_text ? report.activity_other_text : a}</span>)}
          </div>
        </div>
      )}
      {report.main_challenge && (
        <div style={{ fontSize: 11 }}>
          <div style={{ color: C.textMuted, fontSize: 10 }}>Main challenge</div>
          <div style={{ color: C.text, marginTop: 1 }}>{report.main_challenge}</div>
        </div>
      )}
    </div>
  );
}

export default function GemReview({ user }) {
  const canReview = user?.role === 'gem_district_officer';   // admins view only
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);   // full report detail
  const [detailLoading, setDetailLoading] = useState(false);
  const [statusF, setStatusF] = useState('all');
  const [toast, setToast] = useState(null);

  const load = () => {
    setLoading(true);
    gemReportsApi.list()
      .then(r => setRows(Array.isArray(r) ? r : []))
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  };
  useEffect(load, []);

  const open = (id) => {
    setDetailLoading(true);
    gemReportsApi.get(id)
      .then(r => setExpanded(r))
      .catch(() => setToast('Could not load report'))
      .finally(() => setDetailLoading(false));
  };

  const review = async (id) => {
    try {
      await gemReportsApi.review(id);
      setToast('Report marked as reviewed');
      setExpanded(e => e && e.id === id ? { ...e, status: 'reviewed' } : e);
      load();
    } catch (e) {
      setToast(e.message || 'Could not mark reviewed');
    }
    setTimeout(() => setToast(null), 3000);
  };

  const filtered = useMemo(
    () => statusF === 'all' ? rows : rows.filter(r => r.status === statusF),
    [rows, statusF]);

  const counts = useMemo(() => ({
    all: rows.length,
    submitted: rows.filter(r => r.status === 'submitted').length,
    reviewed: rows.filter(r => r.status === 'reviewed').length,
  }), [rows]);

  return (
    <main style={{ flex: 1, padding: '18px 22px', overflow: 'auto', minWidth: 0 }}>
      {toast && (
        <div style={{ position: 'fixed', top: 16, left: '50%', transform: 'translateX(-50%)', background: C.text, color: C.white, padding: '8px 18px', borderRadius: 8, fontSize: 12, zIndex: 9999 }}>{toast}</div>
      )}
      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: 16, fontWeight: 600 }}>GEM Coordinator Submissions</div>
        <div style={{ fontSize: 11, color: C.textSec, marginTop: 3 }}>
          Review monthly reports{user?.district_name ? ` for ${user.district_name} district` : ''}.
        </div>
      </div>

      <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
        {[['all', 'All'], ['submitted', 'Awaiting review'], ['reviewed', 'Reviewed']].map(([k, lbl]) => (
          <button key={k} onClick={() => setStatusF(k)} style={{
            fontSize: 11, padding: '5px 12px', borderRadius: 6, cursor: 'pointer',
            border: `1px solid ${statusF === k ? C.blue600 : C.border}`,
            background: statusF === k ? C.blueBg : C.white, color: statusF === k ? C.blue600 : C.textSec,
            fontWeight: statusF === k ? 600 : 400,
          }}>{lbl} ({counts[k] ?? 0})</button>
        ))}
      </div>

      {loading ? (
        <div style={{ fontSize: 12, color: C.textSec, padding: '20px 0' }}>Loading submissions…</div>
      ) : filtered.length === 0 ? (
        <div style={{ fontSize: 12, color: C.textMuted, padding: '20px 0', fontStyle: 'italic' }}>No submissions to show.</div>
      ) : (
        <div style={{ border: `1px solid ${C.border}`, borderRadius: 8, overflow: 'hidden' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.4fr 1fr 90px 100px 120px', gap: 0, fontSize: 10, fontWeight: 600, color: C.textSec, textTransform: 'uppercase', letterSpacing: '.04em', padding: '9px 14px', background: '#f8fafc', borderBottom: `1px solid ${C.border}` }}>
            <div>Month</div><div>Coordinator</div><div>District</div><div>Schools</div><div>Participants</div><div>Status</div>
          </div>
          {filtered.map(r => (
            <React.Fragment key={r.id}>
              <div onClick={() => expanded?.id === r.id ? setExpanded(null) : open(r.id)}
                style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.4fr 1fr 90px 100px 120px', gap: 0, fontSize: 11, padding: '10px 14px', borderBottom: `1px solid ${C.borderLight}`, alignItems: 'center', cursor: 'pointer', background: expanded?.id === r.id ? C.blueBg : C.white }}>
                <div style={{ fontWeight: 500 }}>{fmtMonth(r.reporting_month)}</div>
                <div style={{ color: C.textSec }}>{r.coordinator_name}</div>
                <div style={{ color: C.textSec }}>{r.district_name || '—'}</div>
                <div>{r.schools_covered ?? 0}</div>
                <div>{(r.total_participants ?? 0).toLocaleString()}</div>
                <div><Badge status={r.status} /></div>
              </div>
              {expanded?.id === r.id && !detailLoading && (
                <Detail report={expanded} onReview={review} onClose={() => setExpanded(null)} canReview={canReview} />
              )}
            </React.Fragment>
          ))}
        </div>
      )}
    </main>
  );
}
