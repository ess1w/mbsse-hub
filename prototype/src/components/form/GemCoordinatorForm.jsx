import React, { useState } from 'react';
import { C } from '../../tokens.js';
import { gemReportsApi } from '../../api/gemReportsApi.js';

// ── Static data ───────────────────────────────────────────────────────────────

const DISTRICTS = [
  'Bo','Bombali','Bonthe','Falaba','Kailahun','Kambia','Karene',
  'Kenema','Koinadugu','Kono','Moyamba','Port Loko','Pujehun',
  'Tonkolili','Western Area Rural','Western Area Urban',
];

// District name → id map (matches DB seed order, 1-indexed)
const DISTRICT_ID = Object.fromEntries(DISTRICTS.map((d, i) => [d, i + 1]));

const ACTIVITIES = [
  'School awareness session',
  'School club activity',
  'Community sensitization',
  'Teacher orientation/training',
  'Radio/media awareness',
  'Parent/PTA meeting',
  'Referral pathway orientation',
  'Other',
];

const IMPL_STATUSES = ['Fully', 'Partially', 'Not implemented'];

const IMPL_REASONS = [
  'Lack of funds',
  'Low participation',
  'Weather/logistics',
  'School schedule conflict',
  'Lack of materials',
  'Other',
];

const KEY_MESSAGES = [
  'Bullying prevention',
  'Prevention of sexual harassment',
  'Alternative discipline/no corporal punishment',
  'Referral/reporting pathways',
  'Child rights/safe schools',
  'Teacher code of conduct',
  'Other',
];

// ── Helpers ───────────────────────────────────────────────────────────────────

const SECTION_TITLES = [
  { num: 1, label: 'Basic Information' },
  { num: 2, label: 'Activity Implementation' },
  { num: 3, label: 'Reach' },
  { num: 4, label: 'Key Outputs' },
  { num: 5, label: 'Challenges' },
];

const EMPTY_FORM = {
  // S1
  reporting_month: '',
  district: DISTRICTS[0],
  coordinator_name: '',
  schools_covered: '',
  // S2
  activities_conducted: [],
  activity_other_text: '',
  total_activities: '',
  impl_status: '',
  impl_reason: '',
  impl_reason_other: '',
  // S3
  total_participants: '',
  girls_reached: '',
  boys_reached: '',
  teachers_parents_community: '',
  teenage_girls: '',
  children_disability: '',
  // S4
  functional_clubs: '',
  srgbv_referrals: '',
  key_messages: [],
  key_message_other_text: '',
  // S5
  main_challenge: '',
};

// ── Shared UI primitives ──────────────────────────────────────────────────────

const label = (text, required = false) => (
  <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: C.textSec, marginBottom: 4 }}>
    {text}{required && <span style={{ color: C.red500, marginLeft: 2 }}>*</span>}
  </label>
);

const inputStyle = (err) => ({
  width: '100%',
  padding: '7px 10px',
  border: `1px solid ${err ? C.red500 : C.border}`,
  borderRadius: 6,
  fontSize: 13,
  color: C.text,
  background: C.white,
  boxSizing: 'border-box',
  outline: 'none',
});

const fieldWrap = { marginBottom: 16 };

function NumericField({ label: lbl, name, value, onChange, error, required }) {
  return (
    <div style={fieldWrap}>
      {label(lbl, required)}
      <input
        type="number" min="0"
        name={name}
        value={value}
        onChange={onChange}
        style={inputStyle(error)}
      />
      {error && <p style={{ fontSize: 11, color: C.red500, marginTop: 3 }}>{error}</p>}
    </div>
  );
}

function CheckGroup({ options, selected, onChange, name }) {
  const toggle = (opt) => {
    const next = selected.includes(opt) ? selected.filter(v => v !== opt) : [...selected, opt];
    onChange(name, next);
  };
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {options.map(opt => (
        <label key={opt} style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13 }}>
          <input
            type="checkbox"
            checked={selected.includes(opt)}
            onChange={() => toggle(opt)}
            style={{ accentColor: C.blue700, width: 14, height: 14 }}
          />
          {opt}
        </label>
      ))}
    </div>
  );
}

function RadioGroup({ options, value, onChange, name }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {options.map(opt => (
        <label key={opt} style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13 }}>
          <input
            type="radio"
            name={name}
            value={opt}
            checked={value === opt}
            onChange={() => onChange(name, opt)}
            style={{ accentColor: C.blue700, width: 14, height: 14 }}
          />
          {opt}
        </label>
      ))}
    </div>
  );
}

function SectionCard({ num, title, children }) {
  return (
    <div style={{
      background: C.white,
      border: `1px solid ${C.border}`,
      borderRadius: 10,
      marginBottom: 20,
      overflow: 'hidden',
    }}>
      <div style={{
        background: C.blue900,
        color: C.white,
        padding: '10px 20px',
        fontSize: 13,
        fontWeight: 700,
        display: 'flex',
        alignItems: 'center',
        gap: 10,
      }}>
        <span style={{
          background: 'rgba(255,255,255,0.18)',
          borderRadius: '50%',
          width: 22, height: 22,
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 11, fontWeight: 800,
        }}>{num}</span>
        {title}
      </div>
      <div style={{ padding: 20 }}>{children}</div>
    </div>
  );
}

// ── Validation ────────────────────────────────────────────────────────────────

function validate(form) {
  const errs = {};
  if (!form.reporting_month) errs.reporting_month = 'Required';
  if (!form.coordinator_name.trim()) errs.coordinator_name = 'Required';
  if (form.schools_covered === '' || isNaN(Number(form.schools_covered))) errs.schools_covered = 'Required';
  if (form.total_activities === '' || isNaN(Number(form.total_activities))) errs.total_activities = 'Required';
  if (!form.impl_status) errs.impl_status = 'Required';
  if (['Partially', 'Not implemented'].includes(form.impl_status) && !form.impl_reason)
    errs.impl_reason = 'Required when not fully implemented';
  if (form.impl_reason === 'Other' && !form.impl_reason_other.trim())
    errs.impl_reason_other = 'Please specify';
  if (form.activities_conducted.includes('Other') && !form.activity_other_text.trim())
    errs.activity_other_text = 'Please specify';
  if (form.key_messages.includes('Other') && !form.key_message_other_text.trim())
    errs.key_message_other_text = 'Please specify';
  return errs;
}

// ── Main component ────────────────────────────────────────────────────────────

export default function GemCoordinatorForm({ user, setActivePage }) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [saveStatus, setSaveStatus] = useState('');  // '' | 'saving' | 'saved' | 'error'
  const [submitted, setSubmitted] = useState(false);

  const set = (name, value) => {
    setForm(prev => ({ ...prev, [name]: value }));
    if (errors[name]) setErrors(prev => { const e = { ...prev }; delete e[name]; return e; });
  };

  const handleChange = (e) => set(e.target.name, e.target.value);

  const handleNumChange = (e) => {
    const val = e.target.value === '' ? '' : Math.max(0, parseInt(e.target.value) || 0);
    set(e.target.name, val);
  };

  // Build the API payload from form state
  const buildPayload = () => ({
    reporting_month: form.reporting_month ? form.reporting_month + '-01' : null,
    district_id: DISTRICT_ID[form.district],
    coordinator_name: form.coordinator_name,
    schools_covered: Number(form.schools_covered) || 0,
    activities_conducted: form.activities_conducted,
    activity_other_text: form.activity_other_text || null,
    total_activities: Number(form.total_activities) || 0,
    impl_status: form.impl_status,
    impl_reason: form.impl_reason || null,
    impl_reason_other: form.impl_reason_other || null,
    total_participants: Number(form.total_participants) || 0,
    girls_reached: Number(form.girls_reached) || 0,
    boys_reached: Number(form.boys_reached) || 0,
    teachers_parents_community: Number(form.teachers_parents_community) || 0,
    teenage_girls: Number(form.teenage_girls) || 0,
    children_disability: Number(form.children_disability) || 0,
    functional_clubs: Number(form.functional_clubs) || 0,
    srgbv_referrals: Number(form.srgbv_referrals) || 0,
    key_messages: form.key_messages,
    key_message_other_text: form.key_message_other_text || null,
    main_challenge: form.main_challenge || null,
  });

  const handleSaveDraft = async () => {
    setSaveStatus('saving');
    try {
      await gemReportsApi.create(buildPayload());
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus(''), 3000);
    } catch {
      setSaveStatus('error');
    }
  };

  const handleSubmit = async () => {
    const errs = validate(form);
    if (Object.keys(errs).length) {
      setErrors(errs);
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }
    setSubmitting(true);
    try {
      const created = await gemReportsApi.create(buildPayload());
      await gemReportsApi.submit(created.id);
      setSubmitted(true);
    } catch {
      setErrors({ _global: 'Submission failed. Please try again.' });
    } finally {
      setSubmitting(false);
    }
  };

  // ── Success screen ────────────────────────────────────────────────────────
  if (submitted) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', background: C.bg }}>
        <div style={{ background: C.white, border: `1px solid ${C.border}`, borderRadius: 12, padding: 48, maxWidth: 480, textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>✅</div>
          <h2 style={{ margin: '0 0 8px', color: C.green700 }}>Report Submitted</h2>
          <p style={{ color: C.textSec, margin: '0 0 24px' }}>
            Your GEM Coordinator monthly report has been submitted successfully.
          </p>
          <button
            onClick={() => { setForm(EMPTY_FORM); setSubmitted(false); }}
            style={{ padding: '9px 24px', background: C.blue700, color: C.white, border: 'none', borderRadius: 7, fontSize: 13, fontWeight: 600, cursor: 'pointer', marginRight: 12 }}
          >
            Submit Another
          </button>
          <button
            onClick={() => setActivePage('gem-home')}
            style={{ padding: '9px 24px', background: C.bg, color: C.text, border: `1px solid ${C.border}`, borderRadius: 7, fontSize: 13, cursor: 'pointer' }}
          >
            Go to Home
          </button>
        </div>
      </div>
    );
  }

  // ── Form ──────────────────────────────────────────────────────────────────
  const showReason = ['Partially', 'Not implemented'].includes(form.impl_status);

  return (
    <div style={{ flex: 1, overflowY: 'auto', background: C.bg, padding: '24px 32px' }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: C.blue900 }}>
          GEM Coordinator Monthly Report
        </h1>
        <p style={{ margin: '4px 0 0', fontSize: 13, color: C.textSec }}>
          Complete all sections and submit at the end of each reporting month.
        </p>
      </div>

      {/* Global error */}
      {errors._global && (
        <div style={{ background: C.redBg, border: `1px solid ${C.red100}`, borderRadius: 8, padding: '10px 16px', marginBottom: 20, color: C.red700, fontSize: 13 }}>
          {errors._global}
        </div>
      )}

      {/* Section 1: Basic Information */}
      <SectionCard num={1} title="Basic Information">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div style={fieldWrap}>
            {label('Reporting Month', true)}
            <input
              type="month"
              name="reporting_month"
              value={form.reporting_month}
              onChange={handleChange}
              style={inputStyle(errors.reporting_month)}
            />
            {errors.reporting_month && <p style={{ fontSize: 11, color: C.red500, marginTop: 3 }}>{errors.reporting_month}</p>}
          </div>

          <div style={fieldWrap}>
            {label('District', true)}
            <select
              name="district"
              value={form.district}
              onChange={handleChange}
              style={{ ...inputStyle(false), height: 34 }}
            >
              {DISTRICTS.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>

          <div style={fieldWrap}>
            {label('Name of GEM Coordinator', true)}
            <input
              type="text"
              name="coordinator_name"
              value={form.coordinator_name}
              onChange={handleChange}
              placeholder="Full name"
              style={inputStyle(errors.coordinator_name)}
            />
            {errors.coordinator_name && <p style={{ fontSize: 11, color: C.red500, marginTop: 3 }}>{errors.coordinator_name}</p>}
          </div>

          <NumericField
            label="Number of schools covered this month"
            name="schools_covered"
            value={form.schools_covered}
            onChange={handleNumChange}
            error={errors.schools_covered}
            required
          />
        </div>
      </SectionCard>

      {/* Section 2: Activity Implementation */}
      <SectionCard num={2} title="Activity Implementation">
        <div style={fieldWrap}>
          {label('Which activities were conducted this month? (Select all that apply)', true)}
          <CheckGroup
            options={ACTIVITIES}
            selected={form.activities_conducted}
            onChange={set}
            name="activities_conducted"
          />
          {form.activities_conducted.includes('Other') && (
            <div style={{ marginTop: 10 }}>
              {label('Please specify')}
              <input
                type="text"
                name="activity_other_text"
                value={form.activity_other_text}
                onChange={handleChange}
                style={inputStyle(errors.activity_other_text)}
              />
              {errors.activity_other_text && <p style={{ fontSize: 11, color: C.red500, marginTop: 3 }}>{errors.activity_other_text}</p>}
            </div>
          )}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <NumericField
            label="How many activities were conducted in total this month?"
            name="total_activities"
            value={form.total_activities}
            onChange={handleNumChange}
            error={errors.total_activities}
            required
          />
        </div>

        <div style={fieldWrap}>
          {label('Were activities implemented as planned?', true)}
          <RadioGroup
            options={IMPL_STATUSES}
            value={form.impl_status}
            onChange={set}
            name="impl_status"
          />
          {errors.impl_status && <p style={{ fontSize: 11, color: C.red500, marginTop: 3 }}>{errors.impl_status}</p>}
        </div>

        {showReason && (
          <div style={fieldWrap}>
            {label('If partially/not implemented, what was the main reason?', true)}
            <RadioGroup
              options={IMPL_REASONS}
              value={form.impl_reason}
              onChange={set}
              name="impl_reason"
            />
            {errors.impl_reason && <p style={{ fontSize: 11, color: C.red500, marginTop: 3 }}>{errors.impl_reason}</p>}
            {form.impl_reason === 'Other' && (
              <div style={{ marginTop: 10 }}>
                {label('Please specify')}
                <input
                  type="text"
                  name="impl_reason_other"
                  value={form.impl_reason_other}
                  onChange={handleChange}
                  style={inputStyle(errors.impl_reason_other)}
                />
                {errors.impl_reason_other && <p style={{ fontSize: 11, color: C.red500, marginTop: 3 }}>{errors.impl_reason_other}</p>}
              </div>
            )}
          </div>
        )}
      </SectionCard>

      {/* Section 3: Reach */}
      <SectionCard num={3} title="Reach">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <NumericField label="Total number of participants reached" name="total_participants" value={form.total_participants} onChange={handleNumChange} />
          <NumericField label="Number of girls reached" name="girls_reached" value={form.girls_reached} onChange={handleNumChange} />
          <NumericField label="Number of boys reached" name="boys_reached" value={form.boys_reached} onChange={handleNumChange} />
          <NumericField label="Number of teachers / parents / community members reached" name="teachers_parents_community" value={form.teachers_parents_community} onChange={handleNumChange} />
          <NumericField label="Number of teenage girls" name="teenage_girls" value={form.teenage_girls} onChange={handleNumChange} />
          <NumericField label="Number of children with disability" name="children_disability" value={form.children_disability} onChange={handleNumChange} />
        </div>
      </SectionCard>

      {/* Section 4: Key Outputs */}
      <SectionCard num={4} title="Key Outputs">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
          <NumericField label="Number of functional school clubs this month" name="functional_clubs" value={form.functional_clubs} onChange={handleNumChange} />
          <NumericField label="Number of SRGBV cases referred through appropriate channels" name="srgbv_referrals" value={form.srgbv_referrals} onChange={handleNumChange} />
        </div>

        <div style={fieldWrap}>
          {label('Which key messages were promoted this month? (Select all that apply)')}
          <CheckGroup
            options={KEY_MESSAGES}
            selected={form.key_messages}
            onChange={set}
            name="key_messages"
          />
          {form.key_messages.includes('Other') && (
            <div style={{ marginTop: 10 }}>
              {label('Please specify')}
              <input
                type="text"
                name="key_message_other_text"
                value={form.key_message_other_text}
                onChange={handleChange}
                style={inputStyle(errors.key_message_other_text)}
              />
              {errors.key_message_other_text && <p style={{ fontSize: 11, color: C.red500, marginTop: 3 }}>{errors.key_message_other_text}</p>}
            </div>
          )}
        </div>
      </SectionCard>

      {/* Section 5: Challenges */}
      <SectionCard num={5} title="Challenges and Support Needed">
        <div style={fieldWrap}>
          {label('What was the main challenge faced this month?')}
          <textarea
            name="main_challenge"
            value={form.main_challenge}
            onChange={handleChange}
            rows={4}
            placeholder="Describe the main challenge..."
            style={{ ...inputStyle(false), resize: 'vertical', fontFamily: 'inherit' }}
          />
        </div>
      </SectionCard>

      {/* Action bar */}
      <div style={{
        display: 'flex',
        justifyContent: 'flex-end',
        gap: 12,
        padding: '16px 0',
        borderTop: `1px solid ${C.border}`,
      }}>
        {saveStatus === 'saved' && (
          <span style={{ fontSize: 12, color: C.green700, alignSelf: 'center' }}>Draft saved ✓</span>
        )}
        {saveStatus === 'error' && (
          <span style={{ fontSize: 12, color: C.red700, alignSelf: 'center' }}>Save failed</span>
        )}

        <button
          onClick={handleSaveDraft}
          disabled={saveStatus === 'saving'}
          style={{
            padding: '9px 20px',
            background: C.white,
            color: C.blue700,
            border: `1px solid ${C.blue400}`,
            borderRadius: 7,
            fontSize: 13,
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          {saveStatus === 'saving' ? 'Saving…' : 'Save Draft'}
        </button>

        <button
          onClick={handleSubmit}
          disabled={submitting}
          style={{
            padding: '9px 24px',
            background: C.blue700,
            color: C.white,
            border: 'none',
            borderRadius: 7,
            fontSize: 13,
            fontWeight: 600,
            cursor: submitting ? 'wait' : 'pointer',
            opacity: submitting ? 0.7 : 1,
          }}
        >
          {submitting ? 'Submitting…' : 'Submit Report'}
        </button>

        <button
          onClick={() => setActivePage('gem-home')}
          style={{
            padding: '9px 24px',
            background: 'transparent',
            color: C.red700,
            border: `1px solid ${C.red100}`,
            borderRadius: 7,
            fontSize: 13,
            cursor: 'pointer',
          }}
        >
          ✕ Cancel
        </button>
      </div>
    </div>
  );
}
