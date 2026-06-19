import React, { useState, useRef } from 'react';
import { FORM_OBJECTIVES, FOCUS_AREAS, ACTIVITY_TYPES, IMPLEMENTATION_STATUSES, GOV_COUNTERPARTS, REFERRAL_PATHWAYS, BUDGET_STATUSES, DISTRICTS, SECTIONS, TACTICS, INTERVENTION_LEVELS } from '../../data/formData.js';
import { C } from '../../tokens.js';
import { submissionsApi, usesDemoData } from '../../api/client.js';

const PAGE_SECTIONS = {
  1: ['A', 'B', 'C', 'D'],
  2: ['E', 'F', 'G', 'H'],
  3: ['I', 'J', 'K', 'L', 'M'],
};

const COMPLETED_INIT = {};

export default function ReportingForm({ user, setActivePage }) {
  const [currentPage, setCurrentPage] = useState(1);
  const [completedPages, setCompletedPages] = useState([1]);
  const [completedSections, setCompletedSections] = useState(COMPLETED_INIT);
  // Activity template for multi-activity repeater (Section C/D)
  const newActivity = () => ({
    _id: Date.now(),
    focusAreas: [],
    objectives: [],
    tactics: [],
    activityType: '',
    interventionLevels: [],
    activityTitle: '',
    implementationStatus: '',
    description: '',
    plannedVsActual: '',
    startDate: '',
    endDate: '',
    // Section E — output indicators per activity (data dict 5.7)
    schools_pre_primary: 0, schools_primary: 0, schools_jss: 0, schools_sss: 0,
    schools_with_focal_person: 0, schools_with_reporting_protocol: 0,
    schools_with_referral_pathway: 0, schools_held_schoolwide_campaign: 0,
    schools_held_peer_led_session: 0, schools_with_safe_space: 0,
    students_inschool_f: 0, students_inschool_m: 0,
    students_inschool_age_10_14: 0, students_inschool_age_15_19: 0, students_inschool_age_under10: 0,
    students_oos_f: 0, students_oos_m: 0,
    students_oos_age_10_14: 0, students_oos_age_15_19: 0,
    students_disability_f: 0, students_disability_m: 0,
    pregnant_girls: 0, teenage_mothers: 0,
    students_used_reporting_mechanism: 0, students_confident_reporting: 0,
    teachers_f: 0, teachers_m: 0, teachers_demonstrated_grp: 0,
    district_officials_f: 0, district_officials_m: 0,
    central_officials_f: 0, central_officials_m: 0,
    community_members_f: 0, community_members_m: 0,
    community_sessions: 0, policy_dialogue_events: 0,
  });

  const [activities, setActivities] = useState([newActivity()]);
  const [activeActivityIdx, setActiveActivityIdx] = useState(0);

  const [form, setForm] = useState({
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
    project: '',
    district: 'Bo',
    chiefdom: 'Valunia',
    community: 'Gondama',
    school: 'Gondama Secondary School',
    emisCode: '10042',
  });

  // Helpers for per-activity field updates
  const setActivityField = (idx, key, val) =>
    setActivities(prev => prev.map((a, i) => i === idx ? { ...a, [key]: val } : a));
  const toggleActivityArr = (idx, key, val) =>
    setActivities(prev => prev.map((a, i) => {
      if (i !== idx) return a;
      return { ...a, [key]: a[key].includes(val) ? a[key].filter(v => v !== val) : [...a[key], val] };
    }));
  const addActivity = () => {
    const next = newActivity();
    setActivities(prev => [...prev, next]);
    setActiveActivityIdx(activities.length);
  };
  const removeActivity = (idx) => {
    setActivities(prev => prev.filter((_, i) => i !== idx));
    setActiveActivityIdx(Math.max(0, Math.min(activeActivityIdx, activities.length - 2)));
  };
  const [autosaveLabel, setAutosaveLabel] = useState('Auto-saved 2 min ago');
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [successToast, setSuccessToast] = useState(false);

  // File upload state (Section K)
  const [uploadedPhotos, setUploadedPhotos] = useState([]);
  const [uploadedDocs,   setUploadedDocs]   = useState([]);
  const [dragOverPhoto,  setDragOverPhoto]  = useState(false);
  const [dragOverDoc,    setDragOverDoc]    = useState(false);
  const photoInputRef = useRef(null);
  const docInputRef   = useRef(null);

  const formatFileSize = (bytes) => {
    if (bytes < 1024)    return `${bytes} B`;
    if (bytes < 1048576) return `${Math.round(bytes / 1024)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  const fileIcon = (name) => {
    const ext = name.split('.').pop().toLowerCase();
    if (['jpg','jpeg','png','gif'].includes(ext)) return '📷';
    if (ext === 'pdf')  return '📄';
    if (['doc','docx'].includes(ext)) return '📝';
    if (['xls','xlsx'].includes(ext)) return '📊';
    return '📎';
  };

  const processPhotoFiles = (files) => {
    const processed = files.map(f => {
      const overSize = f.size > 5 * 1024 * 1024;
      const isImage  = f.type.startsWith('image/');
      return {
        id:        Date.now() + Math.random(),
        name:      f.name,
        sizeLabel: formatFileSize(f.size),
        preview:   isImage && !overSize ? URL.createObjectURL(f) : null,
        rawFile:   f,   // kept for upload on submit
        error:     overSize ? 'Exceeds 5 MB limit — please compress before uploading' : null,
      };
    });
    setUploadedPhotos(prev => [...prev, ...processed]);
    if (photoInputRef.current) photoInputRef.current.value = '';
  };

  const processDocFiles = (files) => {
    const allowed = ['pdf','doc','docx','xls','xlsx'];
    const processed = files.map(f => {
      const ext      = f.name.split('.').pop().toLowerCase();
      const overSize = f.size > 10 * 1024 * 1024;
      const badType  = !allowed.includes(ext);
      return {
        id:        Date.now() + Math.random(),
        name:      f.name,
        sizeLabel: formatFileSize(f.size),
        preview:   null,
        rawFile:   f,   // kept for upload on submit
        error:     overSize ? 'Exceeds 10 MB limit' : badType ? 'File type not supported' : null,
      };
    });
    setUploadedDocs(prev => [...prev, ...processed]);
    if (docInputRef.current) docInputRef.current.value = '';
  };

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

  const handleSubmit = async () => {
    setSubmitError(null);

    // In demo mode (no backend / demo token) just confirm locally.
    if (usesDemoData()) {
      setSubmitted(true);
      setCompletedPages([1, 2, 3]);
      return;
    }

    // Map form state → submission-level API payload
    const payload = {
      project_title:         form.project || null,
      key_results:           form.keyResults || null,
      observed_changes:      form.observedChanges || null,
      early_outcomes:        form.earlyOutcomes || null,
      expenditure:           form.expenditure ? parseFloat(form.expenditure) : null,
      expenditure_currency:  form.currency || 'USD',
      budget_util:           form.budgetStatus || null,
      gov_engaged:           form.govEngaged === 'Yes',
      gov_engaged_list:      form.govCounterpart || null,
      coordination_meetings: Number(form.coordinationMeetings) || 0,
      key_partners:          form.keyPartners || null,
      challenges:            form.challenges || null,
      risks:                 form.risks || null,
      mitigations:           form.mitigations || null,
      safeguarding_cases:    form.safeguardingCases === 'Yes',
      cases_reported:        Number(form.numCases) || 0,
      referral_pathway:      form.referralPathway || null,
      safeguarding_action:   form.actionTaken || null,
      planned_activities:    form.plannedActivities || null,
      support_needed:        form.supportNeeded || null,
    };

    setSubmitting(true);
    try {
      const submission = await submissionsApi.submitReport(payload);
      const subId = submission.id;

      // Upload valid files in parallel (skip any with validation errors)
      const validPhotos = uploadedPhotos.filter(f => !f.error && f.rawFile);
      const validDocs   = uploadedDocs.filter(f => !f.error && f.rawFile);
      if (validPhotos.length + validDocs.length > 0) {
        await Promise.all([
          ...validPhotos.map(f => submissionsApi.uploadFile(subId, f.rawFile, 'photo')),
          ...validDocs.map(f => submissionsApi.uploadFile(subId, f.rawFile, 'document')),
        ]);
      }

      setSuccessToast(true);
      setTimeout(() => {
        setSuccessToast(false);
        handleCancel();
      }, 2000);
    } catch (e) {
      setSubmitError(e.message || 'Submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = () => {
    // Reset every piece of form state back to its initial value
    setCurrentPage(1);
    setCompletedPages([1]);
    setCompletedSections(COMPLETED_INIT);
    setActivities([newActivity()]);
    setActiveActivityIdx(0);
    setSubmitted(false);
    setUploadedPhotos([]);
    setUploadedDocs([]);
    setAutosaveLabel('Auto-saved 2 min ago');
    setForm({
      project: '',
      keyResults: '', observedChanges: '', earlyOutcomes: '',
      expenditure: '', currency: 'USD', budgetStatus: '',
      govEngaged: 'No', govCounterpart: '', coordinationMeetings: 0, keyPartners: '',
      challenges: '', risks: '', mitigations: '',
      safeguardingCases: 'No', numCases: 0, referralPathway: '', actionTaken: '',
      plannedActivities: '', supportNeeded: '',
      district: 'Bo', chiefdom: 'Valunia', community: 'Gondama',
      school: 'Gondama Secondary School', emisCode: '10042',
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
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
      {/* SUCCESS TOAST */}
      {successToast && (
        <div style={{
          position: 'fixed', top: 20, left: '50%', transform: 'translateX(-50%)',
          background: C.green700, color: C.white, padding: '10px 22px', borderRadius: 8,
          fontSize: 13, fontWeight: 500, zIndex: 9999, boxShadow: '0 4px 12px rgba(0,0,0,.2)',
        }}>
          ✓ Report submitted successfully
        </div>
      )}
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
                {user?.org_name ?? 'Your Organisation'} <span style={{ color: C.border }}>|</span> Submitted by: {user?.full_name ?? user?.email ?? '—'}
              </div>
            </div>

            {/* ═══ PAGE 1 ═══ */}
            {currentPage === 1 && (
              <>
                <div style={{ fontSize: 13, fontWeight: 600, color: C.blue600, marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
                  Page 1 of 3 <span style={{ fontSize: 10, fontWeight: 500, padding: '2px 8px', borderRadius: 4, background: C.blueBg, color: C.blue900 }}>Sections A – D · Reporting basics</span>
                </div>

                {/* A — Metadata */}
                {section('A', completedSections.A ? C.green700 : C.blue600, <>
                  <SecHeader id="A" label="Reporting metadata" required done={completedSections.A} systemManaged />
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
                    {compItem('Reporting period', 'Mar–Apr 2026')}
                    {compItem('Organisation', user?.org_name ?? '—')}
                    {fl('Project / programme title', inp('project', 'e.g. Girls Education Programme SL…'))}
                    {compItem('Reporting frequency', 'Bi-monthly')}
                    {compItem('Submission date', <span style={{ fontSize: 10, padding: '2px 7px', background: C.blueBg, color: C.blue900, border: `1px solid ${C.blue100}`, borderRadius: 3 }}>Auto-captured on submit</span>)}
                    {compItem('Status', 'Draft')}
                  </div>
                  {!completedSections.A && (
                    <button onClick={() => setCompletedSections(s => ({ ...s, A: true }))}
                      style={{ marginTop: 10, padding: '6px 14px', fontSize: 11, borderRadius: 5, border: `1px solid ${C.blue600}`, background: C.blueBg, color: C.blue600, cursor: 'pointer', fontWeight: 500 }}>
                      ✓ Confirm metadata
                    </button>
                  )}
                </>)}

                {/* B — Geographic */}
                {section('B', completedSections.B ? C.green700 : C.blue600, <>
                  <SecHeader id="B" label="Geographic coverage" required done={completedSections.B} />
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
                    {fl('District', sel('district', DISTRICTS, null))}
                    {fl('Chiefdom', inp('chiefdom', 'Chiefdom name…'))}
                    {fl('Community / Village', inp('community', 'Community or village…'))}
                    {fl('School name', inp('school', 'School name…'))}
                    {fl('EMIS code', inp('emisCode', 'EMIS code…'))}
                    {fl('GPS coordinates', <div style={{ fontSize: 11, color: C.textMuted, paddingTop: 4 }}>Not captured</div>)}
                  </div>
                  {!completedSections.B && (
                    <button onClick={() => setCompletedSections(s => ({ ...s, B: true }))}
                      style={{ marginTop: 10, padding: '6px 14px', fontSize: 11, borderRadius: 5, border: `1px solid ${C.blue600}`, background: C.blueBg, color: C.blue600, cursor: 'pointer', fontWeight: 500 }}>
                      ✓ Confirm location
                    </button>
                  )}
                </>)}

                {/* C — Activity Classification (multi-activity repeater per v3) */}
                {section('C', C.blue600, <>
                  <SecHeader id="C" label="Activity classification" required />
                  <div style={{ fontSize: 10, color: C.textSec, marginBottom: 10, padding: '6px 10px', background: C.blueBg, borderRadius: 5, border: `1px solid ${C.blue100}` }}>
                    You can report multiple activities. Use the tabs below to add or switch between activities.
                  </div>

                  {/* Activity tabs */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 0, marginBottom: 14, borderBottom: `1px solid ${C.border}` }}>
                    {activities.map((act, idx) => (
                      <div key={act._id} onClick={() => setActiveActivityIdx(idx)} style={{
                        padding: '6px 14px', fontSize: 11, fontWeight: 500, cursor: 'pointer',
                        borderBottom: activeActivityIdx === idx ? `2px solid ${C.blue600}` : '2px solid transparent',
                        color: activeActivityIdx === idx ? C.blue600 : C.textSec,
                        marginBottom: -1, display: 'flex', alignItems: 'center', gap: 6,
                      }}>
                        Activity {idx + 1}
                        {act.activityType && <span style={{ fontSize: 9, color: C.textMuted }}>({act.activityType.split('/')[0].trim()})</span>}
                        {activities.length > 1 && (
                          <span onClick={e => { e.stopPropagation(); removeActivity(idx); }} style={{ fontSize: 10, color: C.red700, cursor: 'pointer', marginLeft: 4 }}>✕</span>
                        )}
                      </div>
                    ))}
                    <button onClick={addActivity} style={{
                      marginLeft: 8, padding: '4px 10px', fontSize: 10, border: `1px dashed ${C.blue600}`,
                      borderRadius: 4, background: 'transparent', color: C.blue600, cursor: 'pointer', whiteSpace: 'nowrap',
                    }}>+ Add activity</button>
                  </div>

                  {/* Active activity fields */}
                  {activities[activeActivityIdx] && (() => {
                    const act = activities[activeActivityIdx];
                    const idx = activeActivityIdx;
                    const multiChip = (key, items) => (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, padding: '6px 8px', border: `1px solid ${C.border}`, borderRadius: 5, minHeight: 34 }}>
                        {items.map(item => (
                          <div key={item} onClick={() => toggleActivityArr(idx, key, item)} style={{
                            fontSize: 10, padding: '3px 8px', borderRadius: 3, cursor: 'pointer', userSelect: 'none',
                            border: `1px solid ${act[key].includes(item) ? C.blue600 : C.border}`,
                            background: act[key].includes(item) ? C.blue600 : C.white,
                            color: act[key].includes(item) ? C.white : C.textSec,
                          }}>{item}</div>
                        ))}
                      </div>
                    );
                    return (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                        {fl('Focus area(s) *', multiChip('focusAreas', FOCUS_AREAS))}
                        <div style={g2}>
                          {fl('Objective(s) *', multiChip('objectives', FORM_OBJECTIVES.map(o => o.full)))}
                          {fl('Tactic(s) *', multiChip('tactics', (TACTICS || FORM_OBJECTIVES.flatMap(o => o.tactics || [])).filter((v, i, a) => a.indexOf(v) === i)))}
                        </div>
                        <div style={g2}>
                          {fl('Activity type *', (
                            <select value={act.activityType} onChange={e => setActivityField(idx, 'activityType', e.target.value)}
                              style={{ width: '100%', height: 33, border: `1px solid ${C.border}`, borderRadius: 5, padding: '0 10px', fontSize: 11 }}>
                              <option value="">Select activity type...</option>
                              {ACTIVITY_TYPES.map(t => <option key={t}>{t}</option>)}
                            </select>
                          ))}
                          {fl('Intervention level(s) *', multiChip('interventionLevels', ['School-based', 'Community-based', 'System-level']))}
                        </div>
                        {/* Section D fields inline with each activity */}
                        <div style={{ borderTop: `1px dashed ${C.border}`, paddingTop: 10 }}>
                          <SecHeader id="D" label="Activity implementation details" required />
                          <div style={g2}>
                            {fl('Activity title *', (
                              <input value={act.activityTitle} onChange={e => setActivityField(idx, 'activityTitle', e.target.value)}
                                placeholder="Enter activity title..." style={{ width: '100%', height: 33, border: `1px solid ${C.border}`, borderRadius: 5, padding: '0 10px', fontSize: 11, boxSizing: 'border-box' }} />
                            ))}
                            {fl('Implementation status *', (
                              <select value={act.implementationStatus} onChange={e => setActivityField(idx, 'implementationStatus', e.target.value)}
                                style={{ width: '100%', height: 33, border: `1px solid ${C.border}`, borderRadius: 5, padding: '0 10px', fontSize: 11 }}>
                                <option value="">Select status...</option>
                                {IMPLEMENTATION_STATUSES.map(s => <option key={s}>{s}</option>)}
                              </select>
                            ))}
                          </div>
                          {fl('Description *', (
                            <textarea value={act.description} onChange={e => setActivityField(idx, 'description', e.target.value)}
                              placeholder="Brief description of the activity this period..." maxLength={500}
                              style={{ width: '100%', height: 64, border: `1px solid ${C.border}`, borderRadius: 5, padding: '8px 10px', fontSize: 11, resize: 'vertical', boxSizing: 'border-box' }} />
                          ), 'max 500 characters')}
                          <div style={g3}>
                            {fl('Planned vs. actual', (
                              <div style={{ display: 'flex', gap: 10 }}>
                                {['As planned', 'Modified'].map(opt => (
                                  <label key={opt} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, cursor: 'pointer' }}>
                                    <input type="radio" checked={act.plannedVsActual === opt} onChange={() => setActivityField(idx, 'plannedVsActual', opt)} /> {opt}
                                  </label>
                                ))}
                              </div>
                            ))}
                            {fl('Start date', (
                              <input type="date" value={act.startDate} onChange={e => setActivityField(idx, 'startDate', e.target.value)}
                                style={{ width: '100%', height: 33, border: `1px solid ${C.border}`, borderRadius: 5, padding: '0 10px', fontSize: 11, boxSizing: 'border-box' }} />
                            ))}
                            {fl('End date', (
                              <input type="date" value={act.endDate} onChange={e => setActivityField(idx, 'endDate', e.target.value)}
                                style={{ width: '100%', height: 33, border: `1px solid ${C.border}`, borderRadius: 5, padding: '0 10px', fontSize: 11, boxSizing: 'border-box' }} />
                            ))}
                          </div>
                        </div>
                      </div>
                    );
                  })()}
                </>)}
              </>
            )}

            {/* ═══ PAGE 2 ═══ */}
            {currentPage === 2 && (
              <>
                <div style={{ fontSize: 13, fontWeight: 600, color: C.blue600, marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
                  Page 2 of 3 <span style={{ fontSize: 10, fontWeight: 500, padding: '2px 8px', borderRadius: 4, background: C.blueBg, color: C.blue900 }}>Sections E – H · Results & coordination</span>
                </div>

                {/* E — Output Indicators (expanded per data dictionary Section 5.7, v3 wireframe) */}
                {section('E', C.blue600, <>
                  <SecHeader id="E" label="Output indicators" required />
                  {infoBanner('Enter totals for this reporting period. Sections apply per activity — use the activity selector above to switch activities.')}

                  {/* Activity selector for Section E */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                    <span style={{ fontSize: 11, color: C.textSec, fontWeight: 500 }}>Entering for:</span>
                    {activities.map((act, idx) => (
                      <button key={act._id} onClick={() => setActiveActivityIdx(idx)} style={{
                        padding: '4px 10px', fontSize: 10, borderRadius: 4, border: `1px solid ${activeActivityIdx === idx ? C.blue600 : C.border}`,
                        background: activeActivityIdx === idx ? C.blue600 : C.white,
                        color: activeActivityIdx === idx ? C.white : C.textSec, cursor: 'pointer',
                      }}>Activity {idx + 1}{act.activityTitle ? ` — ${act.activityTitle.slice(0, 20)}` : ''}</button>
                    ))}
                  </div>

                  {activities[activeActivityIdx] && (() => {
                    const act = activities[activeActivityIdx];
                    const idx = activeActivityIdx;

                    // Card-style number input (label on top, input on bottom) — wireframe pattern
                    const numCard = (label, key) => (
                      <div style={{ border: `1px solid ${C.border}`, borderRadius: 6, padding: '8px 10px', background: '#f8fafc' }}>
                        <div style={{ fontSize: 10, color: C.textSec, fontWeight: 500, marginBottom: 6, lineHeight: 1.3 }}>{label}</div>
                        <input type="number" min="0" value={act[key]}
                          onChange={e => setActivityField(idx, key, parseInt(e.target.value) || 0)}
                          style={{ width: '100%', height: 32, border: `1px solid ${C.border}`, borderRadius: 4, padding: '0 8px', fontSize: 13, textAlign: 'center', boxSizing: 'border-box', color: C.text }} />
                      </div>
                    );

                    // Computed total card (read-only, shows sum of two keys)
                    const totalCard = (label, fKey, mKey) => {
                      const total = (act[fKey] || 0) + (act[mKey] || 0);
                      return (
                        <div style={{ border: `1px solid ${C.blue100}`, borderRadius: 6, padding: '8px 10px', background: C.blueBg }}>
                          <div style={{ fontSize: 10, color: C.textSec, fontWeight: 500, marginBottom: 6, lineHeight: 1.3 }}>{label}</div>
                          <div style={{ height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 15, fontWeight: 700, color: C.blue600 }}>{total}</div>
                        </div>
                      );
                    };

                    // Row-style number input (label left, input right) for mechanisms / engagement
                    const numRow = (label, key) => (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '5px 8px', borderRadius: 4, background: '#f8fafc', fontSize: 11, border: `1px solid ${C.borderLight}` }}>
                        <span style={{ color: C.textSec, flex: 1, paddingRight: 8 }}>{label}</span>
                        <input type="number" min="0" value={act[key]}
                          onChange={e => setActivityField(idx, key, parseInt(e.target.value) || 0)}
                          style={{ width: 64, height: 26, border: `1px solid ${C.border}`, borderRadius: 4, padding: '0 6px', fontSize: 11, textAlign: 'right', flexShrink: 0, color: C.text }} />
                      </div>
                    );

                    const subHead = (text) => (
                      <div style={{ fontSize: 11, fontWeight: 600, color: C.textSec, marginBottom: 8, paddingBottom: 4, borderBottom: `1px solid ${C.border}` }}>{text}</div>
                    );

                    return (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>

                        {/* Schools by level — 4-col card grid */}
                        <div>
                          {subHead('Schools reached — by level')}
                          <div style={g4}>
                            {numCard('Pre-primary', 'schools_pre_primary')}
                            {numCard('Primary', 'schools_primary')}
                            {numCard('Junior Secondary (JSS)', 'schools_jss')}
                            {numCard('Senior Secondary (SSS)', 'schools_sss')}
                          </div>
                        </div>

                        {/* School SRGBV mechanisms — 3 rows × 2 columns (half-width) */}
                        <div>
                          {subHead('School-level SRGBV prevention mechanisms')}
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 5 }}>
                            {numRow('# schools with a trained SRGBV focal person', 'schools_with_focal_person')}
                            {numRow('# schools with SRGBV reporting protocol', 'schools_with_reporting_protocol')}
                            {numRow('# schools with SRGBV referral pathway', 'schools_with_referral_pathway')}
                            {numRow('# schools that held a school-wide SRGBV awareness campaign', 'schools_held_schoolwide_campaign')}
                            {numRow('# schools that held a peer-led SRGBV awareness session', 'schools_held_peer_led_session')}
                            {numRow('# schools with a designated, student-accessible safe space', 'schools_with_safe_space')}
                          </div>
                          {/* Blue KPI info box */}
                          <div style={{ marginTop: 8, background: C.blueBg, border: `1px solid ${C.blue100}`, borderRadius: 5, padding: '7px 12px', fontSize: 10, color: C.blue900, display: 'flex', alignItems: 'flex-start', gap: 7 }}>
                            <span style={{ flexShrink: 0, fontSize: 13 }}>ℹ</span>
                            <span>A school is counted as having a <strong>functional SRGBV mechanism</strong> if it meets ≥ 3 of the 4 criteria (trained focal person, reporting protocol, referral pathway, awareness activities). This KPI is auto-calculated by the system from your inputs.</span>
                          </div>
                        </div>

                        {/* Students — 2-col (in-school | out-of-school), each with Total / F / M / age bands */}
                        <div>
                          {subHead('Students reached')}
                          <div style={g2}>
                            {/* In-school */}
                            <div>
                              <div style={{ fontSize: 10, color: C.textMuted, fontWeight: 600, marginBottom: 6, textTransform: 'uppercase', letterSpacing: '.06em' }}>In-school</div>
                              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6, marginBottom: 6 }}>
                                {totalCard('Total', 'students_inschool_f', 'students_inschool_m')}
                                {numCard('Female', 'students_inschool_f')}
                                {numCard('Male', 'students_inschool_m')}
                              </div>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                {numRow('Age under 10', 'students_inschool_age_under10')}
                                {numRow('Age 10–14', 'students_inschool_age_10_14')}
                                {numRow('Age 15–19', 'students_inschool_age_15_19')}
                              </div>
                            </div>
                            {/* Out-of-school */}
                            <div>
                              <div style={{ fontSize: 10, color: C.textMuted, fontWeight: 600, marginBottom: 6, textTransform: 'uppercase', letterSpacing: '.06em' }}>Out-of-school</div>
                              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6, marginBottom: 6 }}>
                                {totalCard('Total', 'students_oos_f', 'students_oos_m')}
                                {numCard('Female', 'students_oos_f')}
                                {numCard('Male', 'students_oos_m')}
                              </div>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                {numRow('Age 10–14', 'students_oos_age_10_14')}
                                {numRow('Age 15–19', 'students_oos_age_15_19')}
                              </div>
                            </div>
                          </div>

                          {/* Disability & vulnerable — 4-col card grid */}
                          <div style={{ marginTop: 10 }}>
                            <div style={{ fontSize: 10, color: C.textMuted, fontWeight: 600, marginBottom: 6, textTransform: 'uppercase', letterSpacing: '.06em' }}>Disability &amp; vulnerable groups</div>
                            <div style={g4}>
                              {numCard('Students w/ disability — female', 'students_disability_f')}
                              {numCard('Students w/ disability — male', 'students_disability_m')}
                              {numCard('Pregnant girls reached', 'pregnant_girls')}
                              {numCard('Teenage mothers reached', 'teenage_mothers')}
                            </div>
                          </div>
                        </div>

                        {/* Student engagement — full-width rows */}
                        <div>
                          {subHead('Student engagement with SRGBV mechanisms')}
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                            {numRow('# students who used school SRGBV reporting mechanism', 'students_used_reporting_mechanism')}
                            {numRow('# students confident using reporting mechanism', 'students_confident_reporting')}
                          </div>
                        </div>

                        {/* Teachers — 3-col Total/F/M + full-width GRP row */}
                        <div>
                          {subHead('Teachers / school staff trained')}
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6, marginBottom: 8 }}>
                            {totalCard('Total trained', 'teachers_f', 'teachers_m')}
                            {numCard('Female', 'teachers_f')}
                            {numCard('Male', 'teachers_m')}
                          </div>
                          {numRow('# demonstrating non-violent, gender-responsive practices (GRP)', 'teachers_demonstrated_grp')}
                        </div>

                        {/* Government officials — district then central, each 3-col */}
                        <div>
                          {subHead('Government officials trained')}
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                            <div>
                              <div style={{ fontSize: 10, color: C.textMuted, fontWeight: 500, marginBottom: 5 }}>District officials (DDs, SQAM, etc.)</div>
                              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6 }}>
                                {totalCard('Total', 'district_officials_f', 'district_officials_m')}
                                {numCard('Female', 'district_officials_f')}
                                {numCard('Male', 'district_officials_m')}
                              </div>
                            </div>
                            <div>
                              <div style={{ fontSize: 10, color: C.textMuted, fontWeight: 500, marginBottom: 5 }}>Central officials (MBSSE, TSC, etc.)</div>
                              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6 }}>
                                {totalCard('Total', 'central_officials_f', 'central_officials_m')}
                                {numCard('Female', 'central_officials_f')}
                                {numCard('Male', 'central_officials_m')}
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Community members — 3-col Total/F/M */}
                        <div>
                          {subHead('Community members reached')}
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6, marginBottom: 8 }}>
                            {totalCard('Total', 'community_members_f', 'community_members_m')}
                            {numCard('Female', 'community_members_f')}
                            {numCard('Male', 'community_members_m')}
                          </div>
                        </div>

                        {/* Other outputs — full-width rows */}
                        <div>
                          {subHead('Other outputs')}
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                            {numRow('# community sessions conducted', 'community_sessions')}
                            {numRow('# multi-stakeholder policy dialogue events', 'policy_dialogue_events')}
                          </div>
                          <div style={{ marginTop: 8, fontSize: 10, color: C.textMuted, fontStyle: 'italic' }}>
                            Note: count each session / event only once regardless of number of attendees — attendee counts are captured above under community members.
                          </div>
                        </div>

                      </div>
                    );
                  })()}
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

                  {/* Data protection warning */}
                  <div style={{ background: C.redBg, border: `1px solid ${C.red100}`, borderRadius: 5, padding: '8px 12px', fontSize: 11, color: C.red900, marginBottom: 14, lineHeight: 1.5 }}>
                    <strong>Data protection — please read before uploading.</strong> Do not upload any documents or photos containing: names of survivors, victims, or at-risk individuals; case details or incident descriptions; identifiable photos of children; or any personal data about individuals. All uploads must be de-identified.
                  </div>

                  <div style={g2}>

                    {/* ── Photos ── */}
                    <div>
                      <div style={{ fontSize: 11, fontWeight: 600, color: C.textSec, marginBottom: 6 }}>
                        Photos
                        {uploadedPhotos.length > 0 && <span style={{ fontWeight: 400, color: C.textMuted, marginLeft: 6 }}>{uploadedPhotos.length} file{uploadedPhotos.length !== 1 ? 's' : ''}</span>}
                      </div>

                      {/* Hidden file input */}
                      <input ref={photoInputRef} type="file" multiple accept="image/jpeg,image/png,image/gif"
                        style={{ display: 'none' }}
                        onChange={e => processPhotoFiles(Array.from(e.target.files))} />

                      {/* Drop zone */}
                      <div
                        onClick={() => photoInputRef.current?.click()}
                        onDragOver={e => { e.preventDefault(); setDragOverPhoto(true); }}
                        onDragLeave={() => setDragOverPhoto(false)}
                        onDrop={e => { e.preventDefault(); setDragOverPhoto(false); processPhotoFiles(Array.from(e.dataTransfer.files)); }}
                        style={{
                          border: `1.5px dashed ${dragOverPhoto ? C.blue600 : C.border}`,
                          borderRadius: 6, padding: '18px 12px', textAlign: 'center', fontSize: 11,
                          color: dragOverPhoto ? C.blue900 : C.textMuted,
                          background: dragOverPhoto ? C.blueBg : '#f8fafc',
                          cursor: 'pointer', transition: 'all .15s',
                        }}
                      >
                        <div style={{ fontSize: 24, marginBottom: 5 }}>📷</div>
                        {dragOverPhoto ? 'Release to upload' : 'Drop photos here or click to browse'}
                        <div style={{ fontSize: 10, color: C.textMuted, marginTop: 4 }}>JPG, PNG · max 5 MB per file · de-identified only</div>
                      </div>

                      {/* Uploaded file list */}
                      {uploadedPhotos.length > 0 && (
                        <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 5 }}>
                          {uploadedPhotos.map(f => (
                            <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 8px', background: f.error ? C.redBg : C.white, border: `1px solid ${f.error ? C.red100 : C.border}`, borderRadius: 5 }}>
                              {f.preview
                                ? <img src={f.preview} alt="" style={{ width: 30, height: 30, objectFit: 'cover', borderRadius: 3, flexShrink: 0 }} />
                                : <span style={{ fontSize: 18, flexShrink: 0 }}>📷</span>
                              }
                              <div style={{ flex: 1, minWidth: 0 }}>
                                <div style={{ fontSize: 11, fontWeight: 500, color: C.text, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.name}</div>
                                {f.error
                                  ? <div style={{ fontSize: 10, color: C.red700 }}>⚠ {f.error}</div>
                                  : <div style={{ fontSize: 10, color: C.textMuted }}>{f.sizeLabel}</div>
                                }
                              </div>
                              <span onClick={() => setUploadedPhotos(prev => prev.filter(x => x.id !== f.id))}
                                style={{ fontSize: 14, color: C.textMuted, cursor: 'pointer', flexShrink: 0, lineHeight: 1, padding: '0 2px' }}>✕</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* ── Supporting documents ── */}
                    <div>
                      <div style={{ fontSize: 11, fontWeight: 600, color: C.textSec, marginBottom: 6 }}>
                        Supporting documents
                        {uploadedDocs.length > 0 && <span style={{ fontWeight: 400, color: C.textMuted, marginLeft: 6 }}>{uploadedDocs.length} file{uploadedDocs.length !== 1 ? 's' : ''}</span>}
                      </div>

                      {/* Hidden file input */}
                      <input ref={docInputRef} type="file" multiple accept=".pdf,.doc,.docx,.xls,.xlsx"
                        style={{ display: 'none' }}
                        onChange={e => processDocFiles(Array.from(e.target.files))} />

                      {/* Drop zone */}
                      <div
                        onClick={() => docInputRef.current?.click()}
                        onDragOver={e => { e.preventDefault(); setDragOverDoc(true); }}
                        onDragLeave={() => setDragOverDoc(false)}
                        onDrop={e => { e.preventDefault(); setDragOverDoc(false); processDocFiles(Array.from(e.dataTransfer.files)); }}
                        style={{
                          border: `1.5px dashed ${dragOverDoc ? C.blue600 : C.border}`,
                          borderRadius: 6, padding: '18px 12px', textAlign: 'center', fontSize: 11,
                          color: dragOverDoc ? C.blue900 : C.textMuted,
                          background: dragOverDoc ? C.blueBg : '#f8fafc',
                          cursor: 'pointer', transition: 'all .15s',
                        }}
                      >
                        <div style={{ fontSize: 24, marginBottom: 5 }}>📄</div>
                        {dragOverDoc ? 'Release to upload' : 'Drop files here or click to browse'}
                        <div style={{ fontSize: 10, color: C.textMuted, marginTop: 4 }}>PDF, Word, Excel · max 10 MB per file</div>
                      </div>

                      {/* Uploaded file list */}
                      {uploadedDocs.length > 0 && (
                        <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 5 }}>
                          {uploadedDocs.map(f => (
                            <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 8px', background: f.error ? C.redBg : C.white, border: `1px solid ${f.error ? C.red100 : C.border}`, borderRadius: 5 }}>
                              <span style={{ fontSize: 18, flexShrink: 0 }}>{fileIcon(f.name)}</span>
                              <div style={{ flex: 1, minWidth: 0 }}>
                                <div style={{ fontSize: 11, fontWeight: 500, color: C.text, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.name}</div>
                                {f.error
                                  ? <div style={{ fontSize: 10, color: C.red700 }}>⚠ {f.error}</div>
                                  : <div style={{ fontSize: 10, color: C.textMuted }}>{f.sizeLabel}</div>
                                }
                              </div>
                              <span onClick={() => setUploadedDocs(prev => prev.filter(x => x.id !== f.id))}
                                style={{ fontSize: 14, color: C.textMuted, cursor: 'pointer', flexShrink: 0, lineHeight: 1, padding: '0 2px' }}>✕</span>
                            </div>
                          ))}
                        </div>
                      )}
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
              <button onClick={handleCancel} style={{ padding: '8px 14px', background: 'transparent', color: C.red700, border: `1px solid ${C.red100}`, borderRadius: 6, fontSize: 12, cursor: 'pointer' }}>✕ Cancel</button>
            </div>
            <div style={{ fontSize: 11, color: C.textMuted, textAlign: 'center' }}>
              Page {currentPage} of 3 · {completedCount} of {totalSections} sections complete
              {submitError && (
                <div style={{ color: C.red700, marginTop: 3 }}>⚠ {submitError}</div>
              )}
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              {currentPage < 3 && (
                <button onClick={nextPage} style={{ padding: '8px 20px', background: C.blue600, color: C.white, border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 500, cursor: 'pointer' }}>Next page →</button>
              )}
              {currentPage === 3 && !submitted && (
                <button onClick={handleSubmit} disabled={submitting} style={{ padding: '8px 20px', background: submitting ? C.textMuted : C.green700, color: C.white, border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 500, cursor: submitting ? 'not-allowed' : 'pointer' }}>{submitting ? 'Submitting…' : 'Submit report ✓'}</button>
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
