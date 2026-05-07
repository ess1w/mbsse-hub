import React, { useState } from 'react';
import { FORM_OBJECTIVES, FOCUS_AREAS, ACTIVITY_TYPES, IMPLEMENTATION_STATUSES, GOV_COUNTERPARTS, REFERRAL_PATHWAYS, BUDGET_STATUSES, DISTRICTS, SECTIONS } from '../../data/formData.js';
import { C } from '../../tokens.js';

const PAGE_SECTIONS = {
  1: ['A', 'B', 'C', 'D'],
  2: ['E', 'F', 'G', 'H'],
  3: ['I', 'J', 'K', 'L', 'M'],
};

const COMPLETED_INIT = { A: true, B: true };

export default function ReportingForm() {
  const [currentPage, setCurrentPage] = useState(2);
  const [completedPages, setCompletedPages] = useState([1]);
  const [completedSections, setCompletedSections] = useState(COMPLETED_INIT);
  const [form, setForm] = useState({
    focusAreas: ['1. SRGBV Prevention & Response'],
    objective: '',
    tactic: '',
    activityType: 'Training / Capacity Building',
    interventionLevel: 'School-based',
    activityTitle: '',
    implementationStatus: '',
    description: '',
    plannedVsActual: '',
    startDate: '',
    endDate: '',
    schoolsReached: 0,
    teachersTrained: 0,
    studentsReached: 0,
    communitySessions: 0,
    safeSpaces: 0,
    srgbvReferrals: 0,
    disaggFemale: 0,
    disaggMale: 0,
    age1014: 0,
    age1519: 0,
    withDisability: 0,
    outOfSchool: 0,
    keyResults: '',
    observedChanges: '',
    earlyOutcomes: '',
    expenditure: '',
    currency: 'USD',
    budgetStatus: '',
    govEngaged: 'No',
    govCounterpart: '',
    coordinationMeetings: 0,
    keyPartners: '',
    challenges: '',
    risks: '',
    mitigations: '',
    safeguardingCases: 'No',
    numCases: 0,
    referralPathway: '',
    actionTaken: '',
    plannedActivities: '',
    supportNeeded: '',
    district: 'Bo',
    chiefdom: 'Valunia',
    community: 'Gondama',
    school: 'Gondama Secondary School',
    emisCode: '10042',
  });
  const [autosaveLabel, setAutosaveLabel] = useState('Auto-saved 2 min ago');
  const [submitted, setSubmitted] = useState(false);

  const totalSections = 13;
  const completedCount = Object.keys(completedSections).filter(s => completedSections[s]).length;
  const progress = Math.round((completedCount / totalSections) * 100);

  const goPage = (p) => {
    if (p >= 1 && p <= 3) setCurrentPage(p);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const nextPage = () => {
    if (!completedPages.includes(currentPage)) setCompletedPages(prev => [...prev, currentPage]);
    goPage(currentPage + 1);
  };

  const saveDraft = () => {
    setAutosaveLabel('Auto-saved just now');
    setTimeout(() => setAutosaveLabel('Auto-saved 2 min ago'), 2000);
  };

  const handleSubmit = () => {
    setSubmitted(true);
    setCompletedPages([1, 2, 3]);
  };

  const setField = (key, val) => setForm(f => ({ ...f, [key]: val }));
  const toggleFocusArea = (area) => setField('focusAreas',
    form.focusAreas.includes(area)
      ? form.focusAreas.filter(a => a !== area)
      : [...form.focusAreas, area]
  );

  const inp = (key, placeholder, type = 'text') => (
    <input value={form[key]} onChange={e => setField(key, type === 'number' ? Number(e.target.value) : e.target.value)}
      type={type} placeholder={placeholder}
      style={{ width: '100%', height: 33, border: `1px solid ${C.border}`, borderRadius: 5, padding: '0 10px', fontSize: 11, color: C.text, outline: 'none' }} />
  );

  const sel = (key, options, placeholder) => (
    <select value={form[key]} onChange={e => setField(key, e.target.value)}
      style={{ width: '100%', height: 33, border: `1px solid ${C.border}`, borderRadius: 5, padding: '0 10px', fontSize: 11, color: form[key] ? C.text : C.textMuted }}>
      {placeholder && <option value="">{placeholder}</option>}
      {options.map(o => <option key={o} value={o}>{o}</option>)}
    </select>
  );

  const textarea = (key, placeholder, rows = 3) => (
    <textarea value={form[key]} onChange={e => setField(key, e.target.value)} placeholder={placeholder} rows={rows}
      style={{ width: '100%', border: `1px solid ${C.border}`, borderRadius: 5, padding: '7px 10px', fontSize: 11, color: C.text, resize: 'vertical', outline: 'none', fontFamily: 'inherit' }} />
  );

  const numRow = (label, key) => (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', borderRadius: 5, background: '#f8fafc', fontSize: 11, border: `1px solid ${C.borderLight}` }}>
      <span style={{ color: C.textSec }}>{label}</span>
      <input type="number" value={form[key]} onChange={e => setField(key, Number(e.target.value))} min={0}
        style={{ width: 68, height: 27, border: `1px solid ${C.border}`, borderRadius: 4, textAlign: 'right', padding: '0 7px', fontSize: 11, color: C.text }} />
    </div>
  );

  const radio = (key, options) => (
    <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', paddingTop: 4 }}>
      {options.map(opt => (
        <label key={opt} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: C.textSec, cursor: 'pointer' }}>
          <div style={{
            width: 13, height: 13, borderRadius: '50%',
            border: `1.5px solid ${form[key] === opt ? (opt === 'Yes' && key === 'safeguardingCases' ? C.red500 : C.blue600) : C.border}`,
            boxShadow: form[key] === opt ? `inset 0 0 0 3px ${opt === 'Yes' && key === 'safeguardingCases' ? C.red500 : C.blue600}` : 'none',
            flexShrink: 0, cursor: 'pointer',
          }} onClick={() => setField(key, opt)} />
          {opt}
        </label>
      ))}
    </div>
  );

  // Section header
  const SecHeader = ({ id, label, required, done, critical, systemManaged }) => (
    <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{
        width: 20, height: 20, borderRadius: 3, fontSize: 10, fontWeight: 600,
        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
        background: done ? C.green700 : critical ? C.red700 : C.blue600, color: C.white,
      }}>{id}</div>
      {label}
      <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6 }}>
        {done && <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 10, background: C.greenBg, color: C.green900, border: `1px solid ${C.green100}`, fontWeight: 500 }}>✓ Complete</span>}
        {!done && required && !systemManaged && <span style={{ fontSize: 9, padding: '2px 6px', borderRadius: 3, background: C.redBg, color: C.red700, fontWeight: 500 }}>{critical ? 'Critical — required' : 'Required'}</span>}
        {!done && !required && <span style={{ fontSize: 9, padding: '2px 6px', borderRadius: 3, background: C.borderLight, color: C.textMuted, fontWeight: 500 }}>Optional</span>}
        {systemManaged && <span style={{ fontSize: 9, padding: '2px 6px', borderRadius: 3, background: C.blueBg, color: C.blue900, fontWeight: 500 }}>System-managed</span>}
      </div>
    </div>
  );

  const section = (id, borderColor, children) => (
    <div style={{ background: C.white, border: `1px solid ${C.border}`, borderLeft: `3px solid ${borderColor}`, borderRadius: 8, padding: 16, marginBottom: 12 }}>
      {children}
    </div>
  );

  const g2 = { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 };
  const g3 = { display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 };
  const g4 = { display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 10 };
  const fl = (label, children, hint) => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <div style={{ fontSize: 11, fontWeight: 500, color: C.textSec }}>{label}{hint && <span style={{ fontSize: 10, color: C.textMuted, fontWeight: 400, marginLeft: 4 }}>{hint}</span>}</div>
      {children}
    </div>
  );

  const infoBanner = (text) => (
    <div style={{ background: C.blueBg, border: `1px solid ${C.blue100}`, borderRadius: 5, padding: '8px 12px', fontSize: 11, color: C.blue900, marginBottom: 10, display: 'flex', alignItems: 'flex-start', gap: 7, lineHeight: 1.5 }}>
      <span style={{ fontSize: 14, flexShrink: 0 }}>ℹ</span> {text}
    </div>
  );

  const compItem = (label, val) => (
    <div style={{ fontSize: 11 }}>
      <div style={{ color: C.textMuted, fontSize: 10 }}>{label}</div>
      <div style={{ color: C.text, fontWeight: 500, marginTop: 1 }}>{val}</div>
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
      {/* STEPPER */}
      <div style={{
        background: C.white, borderBottom: `1px solid ${C.border}`,
        padding: '0 24px', display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', height: 52,
        position: 'sticky', top: 48, zIndex: 90,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 0 }}>
          {[1, 2, 3].map((p, i) => {
            const isDone = completedPages.includes(p) && p !== currentPage;
            const isActive = p === currentPage;
            return (
              <React.Fragment key={p}>
                <div onClick={() => goPage(p)} style={{ display: 'flex', alignItems: 'center', gap: 8, paddingRight: 16, cursor: 'pointer' }}>
                  <div style={{
                    width: 26, height: 26, borderRadius: '50%',
                    border: `2px solid ${isDone ? C.green700 : isActive ? C.blue600 : C.border}`,
                    background: isDone ? C.green700 : isActive ? C.blue600 : C.white,
                    color: isDone || isActive ? C.white : C.textMuted,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 11, fontWeight: 600, flexShrink: 0,
                  }}>{isDone ? '✓' : p}</div>
                  <span style={{
                    fontSize: 11, fontWeight: 500, whiteSpace: 'nowrap',
                    color: isDone ? C.green700 : isActive ? C.blue600 : C.textMuted,
                  }}>
                    Page {p} — Sections {p === 1 ? 'A–D' : p === 2 ? 'E–H' : 'I–M'}
                  </span>
                </div>
                {i < 2 && <div style={{ width: 40, height: 2, background: completedPages.includes(p) ? C.green700 : C.border, flexShrink: 0, marginRight: 16 }} />}
              </React.Fragment>
            );
          })}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {submitted
            ? <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 4, background: C.greenBg, color: C.green900, border: `1px solid ${C.green100}`, fontWeight: 500 }}>Submitted</span>
            : <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 4, background: C.amberBg, color: C.amber600, border: `1px solid ${C.amber100}`, fontWeight: 500 }}>Draft</span>
          }
          <span style={{ fontSize: 10, color: C.textMuted }}>{autosaveLabel}</span>
        </div>
      </div>

      {/* PROGRESS BAR */}
      <div style={{ height: 3, background: C.blueBg }}>
        <div style={{ height: 3, background: submitted ? C.green700 : C.blue600, width: `${submitted ? 100 : progress}%`, transition: 'width .4s' }} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', flex: 1 }}>
        {/* FORM SIDEBAR */}
        <aside style={{
          background: C.white, borderRight: `1px solid ${C.border}`,
          padding: '12px 0', position: 'sticky', top: 100,
          height: 'calc(100vh - 100px)', overflowY: 'auto',
        }}>
          {[1, 2, 3].map(pg => {
            const isDone = completedPages.includes(pg) && pg !== currentPage;
            const isCurrent = pg === currentPage;
            const badge = isDone ? { label: 'Complete', bg: C.greenBg, color: C.green900 }
              : isCurrent ? { label: 'Current', bg: C.blueBg, color: C.blue900 }
              : { label: 'Upcoming', bg: C.borderLight, color: C.textMuted };
            return (
              <div key={pg} style={{ marginBottom: 4 }}>
                <div style={{ fontSize: 9, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.07em', color: C.textMuted, padding: '8px 14px 3px', display: 'flex', alignItems: 'center', gap: 6 }}>
                  Page {pg}
                  <span style={{ fontSize: 9, padding: '1px 5px', borderRadius: 3, fontWeight: 600, background: badge.bg, color: badge.color }}>{badge.label}</span>
                </div>
                {SECTIONS.filter(s => s.page === pg).map(s => {
                  const isActive = isCurrent && currentPage === pg;
                  const isDoneS = completedSections[s.id];
                  return (
                    <div key={s.id} style={{
                      display: 'flex', alignItems: 'flex-start', gap: 8,
                      padding: '5px 14px', fontSize: 11,
                      color: !isCurrent ? C.textMuted : isDoneS ? C.textMuted : C.textSec,
                      borderLeft: `2px solid ${isActive && !isDoneS ? C.blue600 : 'transparent'}`,
                      background: 'transparent', lineHeight: 1.4,
                    }}>
                      <div style={{
                        width: 16, height: 16, borderRadius: 3, fontSize: 9, fontWeight: 700,
                        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 1,
                        background: isDoneS ? C.green700 : s.critical ? C.red700 : !isCurrent ? C.textMuted : C.blue600,
                        color: C.white,
                      }}>{s.id}</div>
                      {s.label}
                    </div>
                  );
                })}
              </div>
            );
          })}
          <div style={{ padding: '10px 14px', borderTop: `1px solid ${C.borderLight}`, marginTop: 6 }}>
            <div style={{ fontSize: 10, color: C.textMuted, marginBottom: 4 }}>Overall progress</div>
            <div style={{ height: 5, background: C.borderLight, borderRadius: 3, marginBottom: 3 }}>
              <div style={{ height: 5, background: C.green700, borderRadius: 3, width: `${submitted ? 100 : progress}%`, transition: 'width .4s' }} />
            </div>
            <div style={{ fontSize: 10, color: C.textMuted }}>{submitted ? '13 of 13' : `${completedCount} of ${totalSections}`} sections complete</div>
          </div>
        </aside>

        {/* FORM BODY */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ flex: 1, padding: '20px 24px' }}>
            {/* Report heading */}
            <div style={{ marginBottom: 16, paddingBottom: 14, borderBottom: `1px solid ${C.borderLight}` }}>
              <div style={{ fontSize: 16, fontWeight: 600 }}>Bi-monthly Activity Report — March / April 2026</div>
              <div style={{ fontSize: 11, color: C.textSec, marginTop: 4, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                Plan International <span style={{ color: C.border }}>|</span> Submitted by: Salaymatu Kamara <span style={{ color: C.border }}>|</span> Project: Girls Education SL
              </div>
            </div>

            {/* ═══ PAGE 1 ═══ */}
            {currentPage === 1 && (
              <>
                <div style={{ fontSize: 13, fontWeight: 600, color: C.blue600, marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
                  Page 1 of 3 <span style={{ fontSize: 10, fontWeight: 500, padding: '2px 8px', borderRadius: 4, background: C.blueBg, color: C.blue900 }}>Sections A – D · Reporting basics</span>
                </div>

                {/* A — Metadata (completed) */}
                {section('A', C.green700, <>
                  <SecHeader id="A" label="Reporting metadata" required done={completedSections.A} />
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
                    {compItem('Reporting period', 'Mar–Apr 2026')}
                    {compItem('Organisation', 'Plan International')}
                    {compItem('Project', 'Girls Education SL')}
                    {compItem('Reporting frequency', 'Bi-monthly')}
                    {compItem('Submission date', <span style={{ fontSize: 10, padding: '2px 7px', background: C.blueBg, color: C.blue900, border: `1px solid ${C.blue100}`, borderRadius: 3 }}>Auto-captured on submit</span>)}
                    {compItem('Status', 'Draft')}
                  </div>
                </>)}

                {/* B — Geographic (completed) */}
                {section('B', C.green700, <>
                  <SecHeader id="B" label="Geographic coverage" required done={completedSections.B} />
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
                    {compItem('District', 'Bo')}
                    {compItem('Chiefdom', 'Valunia')}
                    {compItem('Community / Village', 'Gondama')}
                    {compItem('School', 'Gondama Secondary School')}
                    {compItem('EMIS code', '10042')}
                    {compItem('GPS coordinates', <span style={{ color: C.textMuted }}>Not captured</span>)}
                  </div>
                </>)}

                {/* C — Activity Classification */}
                {section('C', C.blue600, <>
                  <SecHeader id="C" label="Activity classification" required />
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {fl('Focus area(s) *', (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, padding: '7px 10px', border: `1px solid ${C.border}`, borderRadius: 5, minHeight: 36 }}>
                        {FOCUS_AREAS.map(area => (
                          <div key={area} onClick={() => toggleFocusArea(area)} style={{
                            fontSize: 10, padding: '3px 9px', borderRadius: 3, cursor: 'pointer',
                            border: `1px solid ${form.focusAreas.includes(area) ? C.blue600 : C.border}`,
                            background: form.focusAreas.includes(area) ? C.blue600 : C.white,
                            color: form.focusAreas.includes(area) ? C.white : C.textSec,
                            userSelect: 'none',
                          }}>{area}</div>
                        ))}
                      </div>
                    ))}
                    <div style={g2}>
                      {fl('Objective *', (
                        <div>
                          <select value={form.objective} onChange={e => { setField('objective', e.target.value); setField('tactic', ''); }}
                            style={{ width: '100%', height: 33, border: `1px solid ${C.border}`, borderRadius: 5, padding: '0 10px', fontSize: 11, color: form.objective ? C.text : C.textMuted }}>
                            <option value="">Select objective...</option>
                            {FORM_OBJECTIVES.map(o => <option key={o.short} value={o.short}>{o.full}</option>)}
                          </select>
                          <div style={{ fontSize: 10, color: C.textMuted, marginTop: 3 }}>3 objectives available</div>
                        </div>
                      ))}
                      {fl('Tactic *', 'options update based on objective', (
                        <div style={{ opacity: form.objective ? 1 : 0.4, pointerEvents: form.objective ? 'auto' : 'none' }}>
                          <select value={form.tactic} onChange={e => setField('tactic', e.target.value)}
                            style={{ width: '100%', height: 33, border: `1px solid ${C.border}`, borderRadius: 5, padding: '0 10px', fontSize: 11, color: form.tactic ? C.text : C.textMuted }}>
                            <option value="">{form.objective ? 'Select tactic...' : 'Select objective first...'}</option>
                            {form.objective && FORM_OBJECTIVES.find(o => o.short === form.objective)?.tactics.map(t => <option key={t}>{t}</option>)}
                          </select>
                          {form.tactic && <div style={{ fontSize: 10, color: C.green700, marginTop: 3 }}>Tactic selected ✓</div>}
                        </div>
                      ))}
                    </div>
                    <div style={g2}>
                      {fl('Activity type *', sel('activityType', ACTIVITY_TYPES))}
                      {fl('Intervention level *', radio('interventionLevel', ['School-based', 'Community', 'System-level']))}
                    </div>
                  </div>
                </>)}

                {/* D — Implementation Details */}
                {section('D', C.textMuted, <>
                  <SecHeader id="D" label="Activity implementation details" required />
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <div style={g2}>
                      {fl('Activity title *', inp('activityTitle', 'Enter activity title...'))}
                      {fl('Implementation status *', sel('implementationStatus', IMPLEMENTATION_STATUSES, 'Select status...'))}
                    </div>
                    {fl('Description * ', textarea('description', 'Brief description of the activity this period...'), 'max 500 characters')}
                    <div style={g3}>
                      {fl('Planned vs. actual', radio('plannedVsActual', ['As planned', 'Modified']))}
                      {fl('Start date', inp('startDate', 'DD / MM / YYYY', 'date'))}
                      {fl('End date', inp('endDate', 'DD / MM / YYYY', 'date'))}
                    </div>
                  </div>
                </>)}
              </>
            )}

            {/* ═══ PAGE 2 ═══ */}
            {currentPage === 2 && (
              <>
                <div style={{ fontSize: 13, fontWeight: 600, color: C.blue600, marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
                  Page 2 of 3 <span style={{ fontSize: 10, fontWeight: 500, padding: '2px 8px', borderRadius: 4, background: C.blueBg, color: C.blue900 }}>Sections E – H · Results & coordination</span>
                </div>

                {/* E — Output Indicators */}
                {section('E', C.blue600, <>
                  <SecHeader id="E" label="Output indicators" required />
                  {infoBanner('Enter totals for this reporting period only. Disaggregate by gender and age group where possible.')}
                  <div style={g2}>
                    <div>
                      <div style={{ fontSize: 11, fontWeight: 500, color: C.textSec, marginBottom: 6 }}>Primary outputs</div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {numRow('# schools reached', 'schoolsReached')}
                        {numRow('# teachers trained', 'teachersTrained')}
                        {numRow('# students reached', 'studentsReached')}
                        {numRow('# community sessions', 'communitySessions')}
                        {numRow('# safe spaces set up', 'safeSpaces')}
                        {numRow('# SRGBV referrals', 'srgbvReferrals')}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: 11, fontWeight: 500, color: C.textSec, marginBottom: 6 }}>Disaggregation (students reached)</div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {numRow('Female', 'disaggFemale')}
                        {numRow('Male', 'disaggMale')}
                        {numRow('Age 10–14', 'age1014')}
                        {numRow('Age 15–19', 'age1519')}
                        {numRow('With disability', 'withDisability')}
                        {numRow('Out-of-school', 'outOfSchool')}
                      </div>
                    </div>
                  </div>
                </>)}

                {/* F — Outcome Snapshot */}
                {section('F', C.textMuted, <>
                  <SecHeader id="F" label="Outcome / result snapshot" />
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {fl('Key results this period *', textarea('keyResults', 'What were the main results or achievements this period?...'))}
                    <div style={g2}>
                      {fl('Observed changes', textarea('observedChanges', 'Behavioural, institutional, or community changes observed?...'), 'optional')}
                      {fl('Early outcomes', textarea('earlyOutcomes', 'e.g. improved attendance, increased reporting rates...'), 'optional')}
                    </div>
                  </div>
                </>)}

                {/* G — Financial Tracking */}
                {section('G', C.textMuted, <>
                  <SecHeader id="G" label="Financial tracking" />
                  <div style={g3}>
                    {fl('Monthly expenditure this period', inp('expenditure', 'Enter amount...'))}
                    {fl('Currency', sel('currency', ['USD', 'SLE', 'GBP', 'EUR']))}
                    {fl('Budget utilisation status', sel('budgetStatus', BUDGET_STATUSES, 'Select...'))}
                  </div>
                  <div style={{ marginTop: 10, padding: '8px 10px', background: '#f8fafc', borderRadius: 5, fontSize: 10, color: C.textMuted, border: `1px solid ${C.borderLight}` }}>
                    Options: On track / Under-spending / Over-spending
                  </div>
                </>)}

                {/* H — Coordination */}
                {section('H', C.textMuted, <>
                  <SecHeader id="H" label="Coordination & partnerships" />
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <div style={g2}>
                      {fl('Government counterpart engaged this period?', radio('govEngaged', ['Yes', 'No']))}
                      {fl('Which government counterpart(s)?', (
                        <div style={{ opacity: form.govEngaged === 'Yes' ? 1 : 0.5, pointerEvents: form.govEngaged === 'Yes' ? 'auto' : 'none' }}>
                          {sel('govCounterpart', GOV_COUNTERPARTS, 'Select (if yes above)...')}
                        </div>
                      ))}
                    </div>
                    <div style={g2}>
                      {fl('Coordination meetings attended', inp('coordinationMeetings', '0', 'number'))}
                      {fl('Key partners involved this period', inp('keyPartners', 'Enter partner names...'))}
                    </div>
                  </div>
                </>)}
              </>
            )}

            {/* ═══ PAGE 3 ═══ */}
            {currentPage === 3 && (
              <>
                <div style={{ fontSize: 13, fontWeight: 600, color: C.blue600, marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
                  Page 3 of 3 <span style={{ fontSize: 10, fontWeight: 500, padding: '2px 8px', borderRadius: 4, background: C.blueBg, color: C.blue900 }}>Sections I – M · Challenges, safeguarding & handover</span>
                </div>

                {/* I — Challenges & Risks */}
                {section('I', C.textMuted, <>
                  <SecHeader id="I" label="Challenges & risks" />
                  <div style={g3}>
                    {fl('Key challenges faced', textarea('challenges', 'Describe any challenges encountered this period...'))}
                    {fl('Risks identified', textarea('risks', 'Any risks that may affect future activities?...'))}
                    {fl('Mitigation actions taken', textarea('mitigations', 'Steps taken to address challenges or risks...'))}
                  </div>
                </>)}

                {/* J — Safeguarding (Critical) */}
                {section('J', C.red500, <>
                  <SecHeader id="J" label="Safeguarding & incident reporting" required critical />
                  <div style={{ background: C.redBg, border: `1px solid ${C.red100}`, borderRadius: 5, padding: '8px 12px', fontSize: 11, color: C.red900, marginBottom: 10, lineHeight: 1.5 }}>
                    ⚠ All SRGBV or safeguarding cases must be reported here. Do not include any personal identifying information about individuals in this form.
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {fl('Any SRGBV / safeguarding cases to report this period? *', radio('safeguardingCases', ['Yes', 'No']))}
                    <div style={{
                      padding: 12, borderRadius: 5, background: '#f8fafc', borderLeft: `3px solid ${C.red500}`,
                      opacity: form.safeguardingCases === 'Yes' ? 1 : 0.35,
                      pointerEvents: form.safeguardingCases === 'Yes' ? 'auto' : 'none',
                      transition: 'opacity .2s',
                    }}>
                      <div style={{ fontSize: 10, color: C.textMuted, marginBottom: 8, fontStyle: 'italic' }}>Complete if "Yes" selected above</div>
                      <div style={g3}>
                        {fl('# of cases', inp('numCases', '0', 'number'))}
                        {fl('Referral pathway used', sel('referralPathway', REFERRAL_PATHWAYS, 'Select pathway...'))}
                        {fl('Action taken', inp('actionTaken', 'Describe action taken...'))}
                      </div>
                    </div>
                  </div>
                </>)}

                {/* K — Evidence Uploads */}
                {section('K', C.textMuted, <>
                  <SecHeader id="K" label="Evidence uploads" />
                  <div style={g2}>
                    <div>
                      <div style={{ fontSize: 11, fontWeight: 500, color: C.textSec, marginBottom: 6 }}>Photos</div>
                      <div style={{
                        border: '1.5px dashed #e2e8f0', borderRadius: 6, padding: 18,
                        textAlign: 'center', fontSize: 11, color: C.textMuted, background: '#f8fafc', cursor: 'pointer',
                      }}
                        onMouseEnter={e => { e.currentTarget.style.borderColor = C.blue600; e.currentTarget.style.background = C.blueBg; e.currentTarget.style.color = C.blue900; }}
                        onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.background = '#f8fafc'; e.currentTarget.style.color = C.textMuted; }}>
                        <div style={{ fontSize: 22, marginBottom: 5 }}>📷</div>
                        Drop photos here or click to browse
                        <div style={{ fontSize: 10, color: C.textMuted, marginTop: 4 }}>JPG, PNG · max 5MB per file</div>
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: 11, fontWeight: 500, color: C.textSec, marginBottom: 6 }}>Supporting documents</div>
                      <div style={{
                        border: '1.5px dashed #e2e8f0', borderRadius: 6, padding: 18,
                        textAlign: 'center', fontSize: 11, color: C.textMuted, background: '#f8fafc', cursor: 'pointer',
                      }}
                        onMouseEnter={e => { e.currentTarget.style.borderColor = C.blue600; e.currentTarget.style.background = C.blueBg; e.currentTarget.style.color = C.blue900; }}
                        onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.background = '#f8fafc'; e.currentTarget.style.color = C.textMuted; }}>
                        <div style={{ fontSize: 22, marginBottom: 5 }}>📄</div>
                        Drop files here or click to browse
                        <div style={{ fontSize: 10, color: C.textMuted, marginTop: 4 }}>PDF, Word, Excel · max 10MB per file</div>
                      </div>
                    </div>
                  </div>
                </>)}

                {/* L — Next Period Plan */}
                {section('L', C.textMuted, <>
                  <SecHeader id="L" label="Next period plan" />
                  <div style={g2}>
                    {fl('Planned activities for next period', textarea('plannedActivities', 'Describe activities planned for May–Jun 2026...'))}
                    {fl('Support needed from MBSSE or partners', textarea('supportNeeded', 'What support would help you deliver next period?...'))}
                  </div>
                </>)}

                {/* M — Data Quality */}
                {section('M', C.textMuted, <>
                  <SecHeader id="M" label="Data quality & verification" systemManaged />
                  {infoBanner('The fields below are auto-populated by the system. Admin staff can update verification status and add review flags after submission.')}
                  <div style={g3}>
                    {fl('Submitted by', (
                      <div style={{ height: 33, border: `1px solid ${C.border}`, borderRadius: 5, padding: '0 10px', fontSize: 11, color: C.text, display: 'flex', alignItems: 'center', background: C.white }}>
                        Salaymatu Kamara <span style={{ fontSize: 10, padding: '2px 7px', background: C.blueBg, color: C.blue900, border: `1px solid ${C.blue100}`, borderRadius: 3, marginLeft: 6 }}>Auto</span>
                      </div>
                    ))}
                    {fl('Verified by', <div style={{ height: 33, border: `1px solid ${C.border}`, borderRadius: 5, padding: '0 10px', fontSize: 11, color: C.textMuted, display: 'flex', alignItems: 'center', background: C.white }}>Filled by Admin after review...</div>)}
                    {fl('Flag for review', <div style={{ height: 33, border: `1px solid ${C.border}`, borderRadius: 5, padding: '0 10px', fontSize: 11, color: C.textMuted, display: 'flex', alignItems: 'center', background: C.white, opacity: 0.5 }}>Admin only ▾</div>)}
                  </div>
                </>)}
              </>
            )}
          </div>

          {/* FOOTER ACTIONS */}
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '12px 24px', background: C.white, borderTop: `1px solid ${C.border}`,
            position: 'sticky', bottom: 0, zIndex: 50, boxShadow: '0 -2px 8px rgba(0,0,0,.04)',
          }}>
            <div style={{ display: 'flex', gap: 8 }}>
              {currentPage > 1 && (
                <button onClick={() => goPage(currentPage - 1)} style={{ padding: '8px 16px', background: C.white, color: C.textSec, border: `1px solid ${C.border}`, borderRadius: 6, fontSize: 12, cursor: 'pointer' }}>← Previous page</button>
              )}
              <button onClick={saveDraft} style={{ padding: '8px 12px', background: 'transparent', color: C.textMuted, border: 'none', fontSize: 12, cursor: 'pointer' }}>Save draft</button>
            </div>
            <div style={{ fontSize: 11, color: C.textMuted, textAlign: 'center' }}>
              Page {currentPage} of 3 · {completedCount} of {totalSections} sections complete
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              {currentPage < 3 && (
                <button onClick={nextPage} style={{ padding: '8px 20px', background: C.blue600, color: C.white, border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 500, cursor: 'pointer' }}>Next page →</button>
              )}
              {currentPage === 3 && !submitted && (
                <button onClick={handleSubmit} style={{ padding: '8px 20px', background: C.green700, color: C.white, border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 500, cursor: 'pointer' }}>Submit report ✓</button>
              )}
              {submitted && (
                <span style={{ padding: '8px 20px', background: C.greenBg, color: C.green700, border: `1px solid ${C.green100}`, borderRadius: 6, fontSize: 12, fontWeight: 500 }}>✓ Submitted!</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
