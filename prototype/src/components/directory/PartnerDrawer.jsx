import React, { useEffect } from 'react';
import { C, pill, statusVariant, objColor } from '../../tokens.js';

export default function PartnerDrawer({ partner: p, onClose }) {
  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose]);

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

        {/* Admin actions */}
        <div style={{ padding: '14px 20px' }}>
          <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.07em', color: C.textMuted, marginBottom: 10 }}>Admin</div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button style={{ padding: '6px 12px', background: C.white, color: C.textSec, border: `1px solid ${C.border}`, borderRadius: 6, fontSize: 11, cursor: 'pointer' }}>Edit profile</button>
            <button style={{ padding: '6px 12px', background: C.white, color: C.textSec, border: `1px solid ${C.border}`, borderRadius: 6, fontSize: 11, cursor: 'pointer' }}>View submissions</button>
            {p.submissionStatus === 'Not submitted' && (
              <button style={{ padding: '6px 12px', background: C.white, color: C.red700, border: `1px solid ${C.red100}`, borderRadius: 6, fontSize: 11, cursor: 'pointer' }}>Send reminder</button>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
