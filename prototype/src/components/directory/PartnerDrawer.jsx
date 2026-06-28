import React, { useEffect, useState } from 'react';
import { C, pill, statusVariant, objColor } from '../../tokens.js';
import { slaApi, remindersApi } from '../../api/client.js';

export default function PartnerDrawer({ partner: p, onClose, isAdmin = false, onEdit }) {
  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose]);

  // SLA documents (admin review)
  const [slaDocs, setSlaDocs] = useState([]);
  const [slaBusy, setSlaBusy] = useState(false);
  const loadSla = () => {
    if (!p.id) return;
    slaApi.list(p.id).then(d => setSlaDocs(Array.isArray(d) ? d : [])).catch(() => {});
  };
  useEffect(loadSla, [p.id]);

  const reviewSla = async (docId, status) => {
    setSlaBusy(true);
    try {
      const notes = status === 'rejected'
        ? (window.prompt('Reason for rejection (optional):') || null)
        : null;
      await slaApi.review(docId, status, notes);
      loadSla();
    } catch (_) { /* surface silently; drawer is read-mostly */ }
    finally { setSlaBusy(false); }
  };

  // Send reminder email to this organisation
  const [reminderBusy, setReminderBusy] = useState(false);
  const [reminderMsg, setReminderMsg] = useState(null);
  const sendReminder = async () => {
    setReminderBusy(true);
    setReminderMsg(null);
    try {
      const r = await remindersApi.send(p.id);
      setReminderMsg({ ok: r.sent, text: r.message || (r.sent ? 'Reminder sent' : 'Could not send') });
    } catch (e) {
      setReminderMsg({ ok: false, text: e.message || 'Could not send reminder' });
    } finally {
      setReminderBusy(false);
    }
  };

  const slaPill = (status) => {
    const map = {
      approved: { bg: C.greenBg, color: C.green, label: 'Approved' },
      rejected: { bg: C.redBg, color: C.red, label: 'Rejected' },
      pending:  { bg: C.amberBg, color: C.amber700, label: 'Pending' },
    };
    const s = map[status] || map.pending;
    return <span style={{ fontSize: 9, padding: '2px 7px', borderRadius: 10, background: s.bg, color: s.color, fontWeight: 600 }}>{s.label}</span>;
  };

  const Section = ({ title, children }) => (
    <div style={{ padding: '14px 20px', borderBottom: `1px solid ${C.borderLight}` }}>
      <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.07em', color: C.textMuted, marginBottom: 10 }}>{title}</div>
      {children}
    </div>
  );

  const Field = ({ label, val, highlight }) => (
    <div style={{ marginBottom: 8 }}>
      <div style={{ fontSize: 10, color: C.textMuted, marginBottom: 2 }}>{label}</div>
      <div style={{ fontSize: 11, color: highlight ? C.blue600 : C.text, fontWeight: 500 }}>{val}</div>
    </div>
  );

  return (
    <>
      <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.15)', zIndex: 79 }} />
      <div style={{
        position: 'fixed', right: 0, top: 48, width: 400,
        height: 'calc(100vh - 48px)', background: C.white,
        borderLeft: `1px solid ${C.border}`, boxShadow: '-4px 0 20px rgba(0,0,0,.08)',
        zIndex: 80, overflowY: 'auto',
      }}>
        {/* Header */}
        <div style={{
          padding: '16px 20px', borderBottom: `1px solid ${C.border}`,
          display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
          position: 'sticky', top: 0, background: C.white, zIndex: 1,
        }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: C.text }}>{p.name}</div>
            <div style={{ fontSize: 11, color: C.textMuted, marginTop: 2 }}>
              {p.type} · {p.projects} project{p.projects !== 1 ? 's' : ''} · <span style={pill(statusVariant(p.submissionStatus))}>{p.submissionStatus}</span>
            </div>
          </div>
          <button onClick={onClose} style={{ fontSize: 18, color: C.textMuted, background: 'none', border: 'none', cursor: 'pointer', padding: 4, lineHeight: 1 }}>✕</button>
        </div>

        {/* Contact */}
        <Section title="Contact">
          <Field label="Focal person" val={p.focalPerson} />
          <Field label="Email" val={p.email} highlight />
          <Field label="Phone" val={p.phone} />
        </Section>

        {/* Programme alignment */}
        <Section title="Programme alignment">
          <div style={{ marginBottom: 8 }}>
            <div style={{ fontSize: 10, color: C.textMuted, marginBottom: 4 }}>Objectives</div>
            <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
              {p.objectives.map(o => (
                <span key={o} style={{ ...objColor(o), fontSize: 10, padding: '3px 8px', borderRadius: 3 }}>{o}</span>
              ))}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 10, color: C.textMuted, marginBottom: 4 }}>Focus areas</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              {p.focusAreas.map(f => (
                <span key={f} style={{ fontSize: 9, padding: '2px 6px', borderRadius: 3, background: C.blueBg, color: C.blue900, border: `1px solid ${C.blue100}` }}>{f}</span>
              ))}
            </div>
          </div>
          <div style={{ marginTop: 10 }}>
            <div style={{ fontSize: 10, color: C.textMuted, marginBottom: 4 }}>Districts</div>
            <div style={{ fontSize: 11, color: C.text }}>{p.districts.join(', ')}</div>
          </div>
        </Section>

        {/* Financials */}
        <Section title="Organisation details">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            <Field label="Total budget" val={p.totalBudget} />
            <Field label="Project period" val={p.projectPeriod} />
            <Field label="Funding source" val={p.fundingSource} />
            <Field label="Govt. counterpart" val={p.govCounterpart} />
            <Field label="SLA status" val={<span style={pill(statusVariant(p.slaStatus))}>{p.slaStatus}</span>} />
          </div>
        </Section>

        {/* This period */}
        <Section title={`This period — Mar/Apr 2026`}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            <Field label="Submission status" val={<span style={pill(statusVariant(p.submissionStatus))}>{p.submissionStatus}</span>} />
            <Field label="Last submitted" val={p.lastSubmitted || '—'} />
            <Field label="Schools reached" val={p.schoolsReached || '—'} />
            <Field label="Beneficiaries" val={p.beneficiaries || '—'} />
          </div>
        </Section>

        {/* Projects */}
        <Section title={`Projects (${p.projects})`}>
          {p.projectList.map((proj, i) => (
            <div key={i} style={{ background: '#f8fafc', borderRadius: 6, padding: 10, marginBottom: 6, border: `1px solid ${C.borderLight}` }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: C.text, marginBottom: 4 }}>{proj.title}</div>
              <div style={{ fontSize: 10, color: C.textSec, lineHeight: 1.5 }}>
                <span style={{ ...objColor(proj.obj), fontSize: 9, padding: '2px 6px', borderRadius: 3, marginRight: 6 }}>{proj.obj}</span>
                🌍 {proj.districts} · 📅 {proj.period} · 💵 {proj.budget}
              </div>
            </div>
          ))}
        </Section>

        {/* SLA documents (admin review) */}
        {isAdmin && (
          <Section title="SLA documents">
            {slaDocs.length === 0
              ? <div style={{ fontSize: 11, color: C.textMuted, fontStyle: 'italic' }}>No SLA document uploaded yet.</div>
              : slaDocs.map(d => (
                  <div key={d.id} style={{ border: `1px solid ${C.borderLight}`, borderRadius: 6, padding: 10, marginBottom: 6 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                      <span style={{ fontSize: 16 }}>📄</span>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: 11, fontWeight: 500, color: C.text, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {d.storage_url ? <a href={d.storage_url} target="_blank" rel="noreferrer" style={{ color: C.blue600, textDecoration: 'none' }}>{d.original_filename}</a> : d.original_filename}
                        </div>
                        <div style={{ fontSize: 9, color: C.textMuted }}>{new Date(d.created_at).toLocaleDateString()}</div>
                      </div>
                      {slaPill(d.status)}
                    </div>
                    {d.status === 'pending' && (
                      <div style={{ display: 'flex', gap: 6 }}>
                        <button disabled={slaBusy} onClick={() => reviewSla(d.id, 'approved')} style={{ padding: '4px 10px', fontSize: 10, borderRadius: 5, border: `1px solid ${C.green100}`, background: C.greenBg, color: C.green, cursor: 'pointer', fontWeight: 500 }}>✓ Approve</button>
                        <button disabled={slaBusy} onClick={() => reviewSla(d.id, 'rejected')} style={{ padding: '4px 10px', fontSize: 10, borderRadius: 5, border: `1px solid ${C.red100}`, background: C.redBg, color: C.red700, cursor: 'pointer', fontWeight: 500 }}>✕ Reject</button>
                      </div>
                    )}
                    {d.review_notes && <div style={{ fontSize: 10, color: C.textMuted, marginTop: 4 }}>Note: {d.review_notes}</div>}
                  </div>
                ))
            }
          </Section>
        )}

        {/* Admin actions */}
        {isAdmin && (
          <div style={{ padding: '14px 20px' }}>
            <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.07em', color: C.textMuted, marginBottom: 10 }}>Admin</div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button onClick={onEdit} style={{ padding: '6px 12px', background: C.white, color: C.blue600, border: `1px solid ${C.blue100}`, borderRadius: 6, fontSize: 11, cursor: 'pointer', fontWeight: 500 }}>Edit profile</button>
              <button style={{ padding: '6px 12px', background: C.white, color: C.textSec, border: `1px solid ${C.border}`, borderRadius: 6, fontSize: 11, cursor: 'pointer' }}>View submissions</button>
              {p.submissionStatus === 'Not submitted' && (
                <button onClick={sendReminder} disabled={reminderBusy} style={{ padding: '6px 12px', background: C.white, color: C.red700, border: `1px solid ${C.red100}`, borderRadius: 6, fontSize: 11, cursor: reminderBusy ? 'default' : 'pointer' }}>
                  {reminderBusy ? 'Sending…' : 'Send reminder'}
                </button>
              )}
            </div>
            {reminderMsg && (
              <div style={{ marginTop: 8, fontSize: 11, color: reminderMsg.ok ? C.green : C.red700 }}>
                {reminderMsg.ok ? '✓ ' : '⚠ '}{reminderMsg.text}
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}
