import React, { useState, useEffect } from 'react';
import { C } from '../../tokens.js';
import { reportingPeriodsApi, usesDemoData } from '../../api/client.js';

const BLANK = { label: '', start_date: '', end_date: '', deadline: '', is_active: false };
const fmt = (d) => d ? new Date(d).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' }) : '—';

export default function ReportingPeriods() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(BLANK);
  const [adding, setAdding] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [toast, setToast] = useState(null);

  const demo = usesDemoData();

  const load = () => {
    setLoading(true);
    reportingPeriodsApi.list()
      .then(r => setRows(Array.isArray(r) ? r : []))
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  };
  useEffect(() => { if (!demo) load(); else setLoading(false); }, []);

  const flash = (msg) => { setToast(msg); setTimeout(() => setToast(null), 3000); };

  const activate = async (id) => {
    setBusy(true);
    try { await reportingPeriodsApi.activate(id); await load(); flash('Active reporting period updated'); }
    catch (e) { flash(e.message || 'Could not activate'); }
    finally { setBusy(false); }
  };

  const remove = async (id) => {
    if (!window.confirm('Delete this reporting period?')) return;
    setBusy(true);
    try { await reportingPeriodsApi.remove(id); await load(); flash('Period deleted'); }
    catch (e) { flash(e.message || 'Could not delete'); }
    finally { setBusy(false); }
  };

  const create = async (e) => {
    e.preventDefault();
    setError('');
    if (!form.label.trim() || !form.start_date || !form.end_date || !form.deadline) {
      setError('Label, start, end and deadline are all required.'); return;
    }
    setBusy(true);
    try {
      await reportingPeriodsApi.create({ ...form, label: form.label.trim() });
      setForm(BLANK); setAdding(false); await load(); flash('Reporting period created');
    } catch (err) {
      setError(err.message || 'Could not create period.');
    } finally { setBusy(false); }
  };

  const inp = { width: '100%', padding: '8px 10px', fontSize: 12, borderRadius: 6, border: `1px solid ${C.border}`, boxSizing: 'border-box', outline: 'none' };
  const lbl = { fontSize: 11, fontWeight: 500, color: C.textSec, marginBottom: 4 };

  return (
    <main style={{ flex: 1, padding: '20px 24px', overflow: 'auto', minWidth: 0, maxWidth: 860 }}>
      {toast && (
        <div style={{ position: 'fixed', top: 16, left: '50%', transform: 'translateX(-50%)', background: C.text, color: C.white, padding: '8px 18px', borderRadius: 8, fontSize: 12, zIndex: 9999 }}>{toast}</div>
      )}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 16 }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 600 }}>Reporting Periods</div>
          <div style={{ fontSize: 11, color: C.textSec, marginTop: 3 }}>Create reporting periods and set which one is currently open for submissions.</div>
        </div>
        {!adding && (
          <button onClick={() => { setAdding(true); setError(''); }} style={{ padding: '8px 16px', background: C.blue600, color: C.white, border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 500, cursor: 'pointer' }}>+ New period</button>
        )}
      </div>

      {demo && (
        <div style={{ background: C.amberBg, border: `1px solid ${C.amber100}`, borderRadius: 8, padding: '10px 14px', fontSize: 12, color: C.amber700, marginBottom: 16 }}>
          Reporting-period management is unavailable in demo mode.
        </div>
      )}

      {adding && (
        <form onSubmit={create} style={{ background: C.white, border: `1px solid ${C.border}`, borderRadius: 8, padding: '16px 18px', marginBottom: 18 }}>
          <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 12 }}>New reporting period</div>
          {error && <div style={{ background: C.redBg, border: `1px solid ${C.red}`, borderRadius: 6, padding: '8px 12px', fontSize: 12, color: C.red, marginBottom: 12 }}>{error}</div>}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div style={{ gridColumn: '1 / -1' }}>
              <div style={lbl}>Label</div>
              <input value={form.label} onChange={e => setForm(f => ({ ...f, label: e.target.value }))} placeholder="e.g. May–Jun 2026" style={inp} />
            </div>
            <div><div style={lbl}>Start date</div><input type="date" value={form.start_date} onChange={e => setForm(f => ({ ...f, start_date: e.target.value }))} style={inp} /></div>
            <div><div style={lbl}>End date</div><input type="date" value={form.end_date} onChange={e => setForm(f => ({ ...f, end_date: e.target.value }))} style={inp} /></div>
            <div><div style={lbl}>Submission deadline</div><input type="date" value={form.deadline} onChange={e => setForm(f => ({ ...f, deadline: e.target.value }))} style={inp} /></div>
            <div style={{ display: 'flex', alignItems: 'flex-end' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: C.text, cursor: 'pointer' }}>
                <input type="checkbox" checked={form.is_active} onChange={e => setForm(f => ({ ...f, is_active: e.target.checked }))} style={{ width: 15, height: 15 }} />
                Make this the active period
              </label>
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 16 }}>
            <button type="button" onClick={() => { setAdding(false); setForm(BLANK); setError(''); }} style={{ padding: '8px 16px', border: `1px solid ${C.border}`, background: C.white, color: C.textSec, borderRadius: 6, fontSize: 12, cursor: 'pointer' }}>Cancel</button>
            <button type="submit" disabled={busy} style={{ padding: '8px 18px', background: busy ? C.borderLight : C.blue600, color: busy ? C.textMuted : C.white, border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 500, cursor: busy ? 'default' : 'pointer' }}>{busy ? 'Saving…' : 'Create period'}</button>
          </div>
        </form>
      )}

      {loading ? (
        <div style={{ fontSize: 12, color: C.textSec, padding: '20px 0' }}>Loading…</div>
      ) : rows.length === 0 ? (
        <div style={{ fontSize: 12, color: C.textMuted, padding: '20px 0', fontStyle: 'italic' }}>No reporting periods yet.</div>
      ) : (
        <div style={{ border: `1px solid ${C.border}`, borderRadius: 8, overflow: 'hidden' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1.4fr 1fr 110px 150px', gap: 0, fontSize: 10, fontWeight: 600, color: C.textSec, textTransform: 'uppercase', letterSpacing: '.04em', padding: '9px 14px', background: '#f8fafc', borderBottom: `1px solid ${C.border}` }}>
            <div>Period</div><div>Dates</div><div>Deadline</div><div>Status</div><div style={{ textAlign: 'right' }}>Actions</div>
          </div>
          {rows.map(p => (
            <div key={p.id} style={{ display: 'grid', gridTemplateColumns: '1.3fr 1.4fr 1fr 110px 150px', gap: 0, fontSize: 12, padding: '10px 14px', borderBottom: `1px solid ${C.borderLight}`, alignItems: 'center' }}>
              <div style={{ fontWeight: 500 }}>{p.label}</div>
              <div style={{ color: C.textSec }}>{fmt(p.start_date)} – {fmt(p.end_date)}</div>
              <div style={{ color: C.textSec }}>{fmt(p.deadline)}</div>
              <div>
                {p.is_active
                  ? <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 10, background: C.greenBg, color: C.green, fontWeight: 600 }}>Active</span>
                  : <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 10, background: C.borderLight, color: C.textMuted, fontWeight: 600 }}>Inactive</span>}
              </div>
              <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
                {!p.is_active && <span onClick={() => !busy && activate(p.id)} style={{ fontSize: 11, color: C.blue600, cursor: 'pointer', fontWeight: 500 }}>Set active</span>}
                {!p.is_active && <span onClick={() => !busy && remove(p.id)} style={{ fontSize: 11, color: C.red700, cursor: 'pointer' }}>Delete</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
