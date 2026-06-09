import React from 'react';
import { C, pill, statusVariant } from '../tokens.js';
import { remindersApi, DEMO_MODE } from '../api/client.js';

const KPI = ({ label, val, sub, subColor, alert }) => (
  <div style={{ background: C.white, borderRadius: 8, padding: '14px 16px', border: `1px solid ${C.border}`, borderLeft: alert ? `3px solid ${C.red500}` : `1px solid ${C.border}` }}>
    <div style={{ fontSize: 11, color: C.textSec, marginBottom: 6, fontWeight: 500 }}>{label}</div>
    <div style={{ fontSize: 26, fontWeight: 600, lineHeight: 1, color: alert ? C.red700 : C.text }}>{val}</div>
    <div style={{ fontSize: 10, marginTop: 5, color: subColor || C.textMuted }}>{sub}</div>
  </div>
);

const Panel = ({ title, annotation, link, children }) => (
  <div style={{ background: C.white, border: `1px solid ${C.border}`, borderRadius: 8, padding: '14px 16px' }}>
    <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 12, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      {title}
      <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
        {annotation && <span style={{ fontSize: 10, fontWeight: 400, padding: '2px 7px', background: C.blueBg, color: C.blue900, borderRadius: 3, border: `1px solid ${C.blue100}` }}>{annotation}</span>}
        {link && <span style={{ fontSize: 11, color: C.blue600, cursor: 'pointer', fontWeight: 500 }}>{link}</span>}
      </div>
    </div>
    {children}
  </div>
);

const AlertItem = ({ variant, icon, children }) => {
  const s = {
    red: { bg: C.redBg, color: C.red900, border: C.red100 },
    amber: { bg: C.amberBg, color: C.amber600, border: C.amber100 },
    blue: { bg: C.blueBg, color: C.blue900, border: C.blue100 },
  }[variant];
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, padding: '8px 10px', borderRadius: 6, fontSize: 11, lineHeight: 1.4, background: s.bg, color: s.color, border: `1px solid ${s.border}` }}>
      <span style={{ fontSize: 12, flexShrink: 0, fontWeight: 700, marginTop: 1 }}>{icon}</span>
      <div>{children}</div>
    </div>
  );
};

const bars = [
  { label: 'SRGBV', val: 214, h: 92 },
  { label: 'MHPSS', val: 144, h: 62 },
  { label: 'Gov.', val: 128, h: 55 },
  { label: 'Life Skills', val: 181, h: 78 },
  { label: 'WASH', val: 88, h: 38 },
  { label: 'Norms', val: 116, h: 50 },
  { label: 'Soc. P.', val: 65, h: 28 },
  { label: 'Other', val: 42, h: 18 },
];
const barColors = ['#185FA5', '#378ADD', '#85B7EB', '#185FA5', '#378ADD', '#85B7EB', '#B5D4F4', '#dbeeff'];

// Stacked bar data for Beneficiaries over time (F/M disaggregation)
const STACKED_DATA = [
  { label: 'Jul–Aug', sub: "'25", f: 10500, m: 7500 },
  { label: 'Sep–Oct', sub: "'25", f: 14000, m: 10000 },
  { label: 'Nov–Dec', sub: "'25", f: 18000, m: 13000 },
  { label: 'Jan–Feb', sub: "'26", f: 24500, m: 17500 },
  { label: 'Mar–Apr', sub: "'26", f: 28000, m: 20300 },
];

const ATTENTION = [
  { name: 'Street Child of Sierra Leone', region: 'Western Area, Port Loko', sla: 'SLA pending', status: 'Not submitted' },
  { name: 'Catholic Relief Services', region: 'Kailahun, Kenema', sla: 'SLA signed', status: 'Not submitted' },
  { name: 'CAUSE Canada', region: 'Bombali, Tonkolili', sla: 'SLA signed', status: 'Not submitted' },
];

const DRAFTS = [
  { name: 'Girl Child Network SL', region: 'Western Area, Bo', started: '14 Apr', days: 66 },
  { name: 'Restless Development SL', region: 'Kenema, Kono', started: '10 Apr', days: 66 },
];

export default function Dashboard({ setActivePage }) {
  const [activeTab, setActiveTab] = React.useState('not-submitted');
  const [reminderState, setReminderState] = React.useState({ loading: false, result: null });

  async function handleSendReminders() {
    if (reminderState.loading) return;
    setReminderState({ loading: true, result: null });
    try {
      if (DEMO_MODE) {
        // Simulate a response in demo mode
        await new Promise(r => setTimeout(r, 800));
        setReminderState({ loading: false, result: { sent: 15, message: '15 reminder(s) sent. (demo)' } });
      } else {
        const result = await remindersApi.sendBulk();
        setReminderState({ loading: false, result });
      }
    } catch (err) {
      setReminderState({ loading: false, result: { sent: 0, message: `Error: ${err.message}` } });
    }
  }

  return (
    <main style={{ flex: 1, padding: '18px 20px', overflow: 'auto' }}>
      <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 3 }}>Dashboard</div>
      <div style={{ fontSize: 11, color: C.textSec, marginBottom: 16 }}>SRGBV Coordination Hub — Last updated: 25 April 2026</div>

      {/* Filter bar */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', background: C.white, padding: '10px 14px', borderRadius: 8, border: `1px solid ${C.border}` }}>
        <span style={{ fontSize: 11, fontWeight: 600, color: C.textSec }}>Filter:</span>
        {['All periods → Mar–Apr 2026', 'All districts', 'All focus areas', 'All objectives', 'All partners'].map((label, i) => (
          <select key={i} style={{ fontSize: 11, padding: '5px 9px', border: `1px solid ${C.border}`, borderRadius: 5, background: C.white, cursor: 'pointer' }}>
            <option>{label}</option>
          </select>
        ))}
        <button style={{ fontSize: 11, padding: '5px 12px', borderRadius: 5, background: C.blue600, color: C.white, border: 'none', cursor: 'pointer', fontWeight: 500 }}>Apply</button>
        <button style={{ fontSize: 11, padding: '5px 10px', borderRadius: 5, background: 'transparent', color: C.textSec, border: `1px solid ${C.border}`, cursor: 'pointer' }}>Reset</button>
        <span style={{ fontSize: 11, color: C.textSec, background: '#f1f5f9', padding: '3px 8px', borderRadius: 4 }}>Mar–Apr 2026 · All districts</span>
      </div>

      {/* Provisional data banner (v3) */}
      <div style={{
        background: '#FFF8E1', border: '1px solid #FFC107', borderRadius: 6,
        padding: '8px 14px', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 10,
      }}>
        <span style={{ fontSize: 14 }}>⚠️</span>
        <div style={{ fontSize: 11, color: '#795548', lineHeight: 1.4 }}>
          <strong>Provisional data</strong> — Mar–Apr 2026 reporting cycle is still open. Figures shown include data from {' '}
          <strong>38 of 53</strong> partners and will change as submissions are received and verified.
          Data marked <em>provisional</em> should not be cited externally.
        </div>
      </div>

      {/* KPIs — 7 cards per v3 wireframe */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7,minmax(0,1fr))', gap: 10, marginBottom: 16 }}>
        <KPI label="Reporting partners" val="38 / 53" sub="+5 onboarded this cycle" subColor={C.green700} />
        <KPI label="Schools reached" val="842" sub="14 districts · provisional" />
        <KPI label="Beneficiaries this period" val="48,310" sub="58% F | 42% M · provisional" />
        <KPI label="Schools w/ functional SRGBV mechanism" val="321" sub="321 of 842 meet ≥3 of 4 criteria" />
        <KPI label="SRGBV cases reported" val="134" sub="Across 9 districts" />
        <KPI label="SRGBV cases referred" val="97" sub="72% referral rate" />
        <KPI label="Reporting compliance" val="72%" sub="15 partners not submitted" alert />
      </div>

      {/* Row: Map + Alerts */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.8fr 1fr', gap: 14, marginBottom: 14 }}>
        <Panel title="Coverage map" annotation="District level · click to drill down" link="Full map →">
          <div style={{ background: '#f8fafc', borderRadius: 6, height: 280, border: `1px solid ${C.border}`, position: 'relative', overflow: 'hidden' }}>
            <svg width="100%" height="100%" viewBox="0 0 430 290" xmlns="http://www.w3.org/2000/svg">
              <polygon points="18.9,138.3 36.9,134.9 47.3,140.0 49.8,146.7 34.4,150.0 21.5,145.0" fill="#185FA5" stroke="#fff" strokeWidth="1.5"/>
              <text x="34.4" y="144.5" fontSize="6.5" fill="#fff" textAnchor="middle" fontFamily="sans-serif" fontWeight="600">W.Area Urban</text>
              <polygon points="18.9,124.0 47.3,126.5 49.8,146.7 34.4,150.0 21.5,145.0 15.0,132.4" fill="#378ADD" stroke="#fff" strokeWidth="1.5"/>
              <text x="31.8" y="137.5" fontSize="6.5" fill="#fff" textAnchor="middle" fontFamily="sans-serif" fontWeight="600">W.A. Rural</text>
              <polygon points="47.3,94.7 96.3,86.3 111.8,103.1 105.3,128.2 79.5,132.4 49.8,126.5 47.3,111.5" fill="#378ADD" stroke="#fff" strokeWidth="1.5"/>
              <text x="75.6" y="112.5" fontSize="7.5" fill="#fff" textAnchor="middle" fontFamily="sans-serif" fontWeight="600">Port Loko</text>
              <polygon points="47.3,52.7 96.3,48.5 111.8,69.5 96.3,86.3 47.3,94.7 36.9,77.9" fill="#85B7EB" stroke="#fff" strokeWidth="1.5"/>
              <text x="73.1" y="73.5" fontSize="7.5" fill="#0C447C" textAnchor="middle" fontFamily="sans-serif">Kambia</text>
              <polygon points="36.9,77.9 47.3,52.7 96.3,48.5 111.8,69.5 96.3,86.3 47.3,94.7" fill="#B5D4F4" stroke="#fff" strokeWidth="1.5"/>
              <text x="60.2" y="76.5" fontSize="7" fill="#0C447C" textAnchor="middle" fontFamily="sans-serif">Karene</text>
              <polygon points="96.3,48.5 176.3,48.5 208.5,56.9 202.1,86.3 163.4,98.9 111.8,103.1 96.3,86.3" fill="#378ADD" stroke="#fff" strokeWidth="1.5"/>
              <text x="153.1" y="76.5" fontSize="7.5" fill="#fff" textAnchor="middle" fontFamily="sans-serif" fontWeight="600">Bombali</text>
              <polygon points="176.3,48.5 273.1,27.6 318.2,48.5 305.3,86.3 273.1,111.5 240.8,94.7 202.1,86.3 208.5,56.9" fill="#FCEBEB" stroke="#E24B4A" strokeWidth="1.5" strokeDasharray="5,3" fillOpacity="0.6"/>
              <text x="247.3" y="68.0" fontSize="7.5" fill="#A32D2D" textAnchor="middle" fontFamily="sans-serif">Koinadugu</text>
              <polygon points="273.1,27.6 369.8,19.2 408.5,44.4 382.7,69.5 318.2,86.3 305.3,48.5" fill="#B5D4F4" stroke="#fff" strokeWidth="1.5"/>
              <text x="337.6" y="52.5" fontSize="7.5" fill="#0C447C" textAnchor="middle" fontFamily="sans-serif">Falaba</text>
              <polygon points="163.4,98.9 202.1,86.3 240.8,94.7 273.1,111.5 266.6,136.6 215.0,153.4 176.3,145.0 150.5,132.4 105.3,128.2 111.8,103.1" fill="#85B7EB" stroke="#fff" strokeWidth="1.5"/>
              <text x="195.6" y="123.0" fontSize="7.5" fill="#0C447C" textAnchor="middle" fontFamily="sans-serif">Tonkolili</text>
              <polygon points="318.2,48.5 408.5,44.4 411.1,94.7 382.7,128.2 344.0,145.0 318.2,136.6 305.3,86.3" fill="#378ADD" stroke="#fff" strokeWidth="1.5"/>
              <text x="359.5" y="92.0" fontSize="7.5" fill="#fff" textAnchor="middle" fontFamily="sans-serif" fontWeight="600">Kailahun</text>
              <polygon points="266.6,136.6 273.1,111.5 305.3,86.3 318.2,136.6 344.0,145.0 337.6,170.2 305.3,191.1 273.1,182.7 266.6,161.8" fill="#378ADD" stroke="#fff" strokeWidth="1.5"/>
              <text x="307.9" y="153.5" fontSize="7.5" fill="#fff" textAnchor="middle" fontFamily="sans-serif" fontWeight="600">Kenema</text>
              <polygon points="337.6,170.2 344.0,145.0 382.7,128.2 411.1,94.7 408.5,153.4 382.7,186.9 356.9,195.3 305.3,191.1" fill="#85B7EB" stroke="#fff" strokeWidth="1.5"/>
              <text x="369.8" y="155.0" fontSize="7.5" fill="#0C447C" textAnchor="middle" fontFamily="sans-serif">Kono</text>
              <polygon points="150.5,132.4 176.3,145.0 215.0,153.4 266.6,161.8 273.1,182.7 240.8,199.5 189.2,199.5 150.5,178.5 124.7,161.8 105.3,128.2" fill="#185FA5" stroke="#fff" strokeWidth="1.5"/>
              <text x="189.2" y="168.0" fontSize="7.5" fill="#fff" textAnchor="middle" fontFamily="sans-serif" fontWeight="600">Bo</text>
              <polygon points="49.8,146.7 79.5,132.4 105.3,128.2 124.7,161.8 150.5,178.5 144.0,203.7 124.7,216.3 86.0,212.1 60.2,195.3 34.4,170.2" fill="#85B7EB" stroke="#fff" strokeWidth="1.5"/>
              <text x="96.3" y="178.0" fontSize="7.5" fill="#0C447C" textAnchor="middle" fontFamily="sans-serif">Moyamba</text>
              <polygon points="189.2,199.5 240.8,199.5 273.1,182.7 305.3,191.1 318.2,216.3 305.3,254.0 266.6,266.6 215.0,262.4 189.2,245.6 176.3,220.5" fill="#B5D4F4" stroke="#fff" strokeWidth="1.5"/>
              <text x="247.3" y="228.0" fontSize="7.5" fill="#0C447C" textAnchor="middle" fontFamily="sans-serif">Pujehun</text>
              <polygon points="86.0,212.1 124.7,216.3 144.0,203.7 176.3,220.5 189.2,245.6 215.0,262.4 215.0,271.5 176.3,271.5 124.7,254.0 92.4,237.3" fill="#FCEBEB" stroke="#E24B4A" strokeWidth="1.5" strokeDasharray="5,3" fillOpacity="0.6"/>
              <text x="155.0" y="248.0" fontSize="7.5" fill="#A32D2D" textAnchor="middle" fontFamily="sans-serif">Bonthe</text>
              <text x="247.3" y="74.0" fontSize="14" fill="#E24B4A" textAnchor="middle" fontFamily="sans-serif" opacity="0.8">✕</text>
              <text x="155.0" y="254.0" fontSize="14" fill="#E24B4A" textAnchor="middle" fontFamily="sans-serif" opacity="0.8">✕</text>
              <text x="22" y="270" fontSize="7" fill="#94a3b8" fontFamily="sans-serif" fontStyle="italic">Atlantic Ocean</text>
              <text x="405" y="20" fontSize="9" fill="#94a3b8" fontFamily="sans-serif" textAnchor="middle">N</text>
              <line x1="405" y1="22" x2="405" y2="32" stroke="#94a3b8" strokeWidth="1"/>
              <polygon points="405,22 402,30 405,28 408,30" fill="#94a3b8"/>
            </svg>
          </div>
          <div style={{ display: 'flex', gap: 12, marginTop: 8, flexWrap: 'wrap' }}>
            {[['#185FA5','5+ partners'],['#378ADD','3–4 partners'],['#85B7EB','1–2 partners'],['#E6F1FB','Data gap'],['#E24B4A','No coverage']].map(([color, label]) => (
              <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 10, color: C.textSec }}>
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: color, flexShrink: 0, border: color === '#E6F1FB' ? `1px solid ${C.blue100}` : 'none' }} />
                {label}
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Alerts & gaps" annotation="Admin only">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
            <AlertItem variant="red" icon="▲"><strong>2 districts</strong> with no active interventions — Koinadugu, Bonthe</AlertItem>
            <AlertItem variant="red" icon="▲"><strong>18 partners</strong> not submitted for Mar–Apr cycle — deadline 30 Jun</AlertItem>
            <AlertItem variant="amber" icon="!"><strong>3 districts</strong> covered by only 1 partner — Falaba, Karene, Pujehun</AlertItem>
            <AlertItem variant="amber" icon="!"><strong>7 activities</strong> reported with zero beneficiaries — flagged for review</AlertItem>
            <AlertItem variant="blue" icon="i"><strong>5 new partners</strong> onboarded this period — pending first submission</AlertItem>
            <AlertItem variant="blue" icon="i"><strong>Next deadline:</strong> 30 June 2026 — reminders sent 20 Jun</AlertItem>
          </div>
        </Panel>
      </div>

      {/* Row: Charts — 2×2 grid matching wireframe */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 14 }}>

        {/* [R1 C1] Activities by focus area — bars with counts on top */}
        <Panel title="Activities by focus area">
          <div style={{ background: '#f8fafc', borderRadius: 6, height: 170, border: `1px solid ${C.border}`, display: 'flex', alignItems: 'flex-end', padding: '20px 8px 0', overflow: 'visible', position: 'relative' }}>
            {bars.map((b, i) => (
              <div key={b.label} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%', justifyContent: 'flex-end' }}>
                <span style={{ fontSize: 9, fontWeight: 600, color: barColors[i] === '#dbeeff' ? C.blue600 : barColors[i], marginBottom: 3 }}>{b.val}</span>
                <div title={`${b.label}: ${b.val}`} style={{ width: '80%', height: `${b.h}%`, background: barColors[i], borderRadius: '3px 3px 0 0' }} />
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-around', paddingTop: 4 }}>
            {bars.map(b => <span key={b.label} style={{ fontSize: 9, color: C.textMuted, textAlign: 'center', flex: 1 }}>{b.label}</span>)}
          </div>
        </Panel>

        {/* [R1 C2] Activities by objective */}
        <Panel title="Activities by objective" annotation="Strategic view">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14, paddingTop: 4 }}>
            {[
              { label: 'Obj 1 — Gender-equitable behaviours', val: 214, pct: 56, color: '#185FA5', partners: 28 },
              { label: 'Obj 2 — Institutional & community capacity', val: 312, pct: 82, color: '#378ADD', partners: 41 },
              { label: 'Obj 3 — Policy enforcement & sustainability', val: 96, pct: 25, color: '#85B7EB', partners: 18 },
            ].map(obj => (
              <div key={obj.label}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 4 }}>
                  <span style={{ color: C.textSec, maxWidth: '75%', lineHeight: 1.3 }}>{obj.label}</span>
                  <span style={{ fontWeight: 600, color: obj.color }}>{obj.val}</span>
                </div>
                <div style={{ height: 10, background: '#f1f5f9', borderRadius: 5, overflow: 'hidden' }}>
                  <div style={{ height: 10, width: `${obj.pct}%`, background: obj.color, borderRadius: 5 }} />
                </div>
                <div style={{ fontSize: 9, color: C.textMuted, marginTop: 2 }}>3 tactics · {obj.partners} partners reporting</div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 14, paddingTop: 8, borderTop: `1px solid ${C.borderLight}`, fontSize: 10, color: C.textMuted }}>
            622 activities total · <span style={{ color: C.blue600, cursor: 'pointer' }}>View by tactic →</span>
          </div>
        </Panel>

        {/* [R2 C1] Beneficiaries over time — stacked bar chart */}
        <Panel title="Beneficiaries over time" annotation="6-month">
          {/* Disaggregation controls */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 10, alignItems: 'center' }}>
            <span style={{ fontSize: 10, color: C.textSec, fontWeight: 500 }}>Break down by:</span>
            <select style={{ fontSize: 10, padding: '3px 7px', border: `1px solid ${C.border}`, borderRadius: 4, background: C.white }}>
              <option>Sex (F / M)</option>
              <option>Beneficiary type (in-school / out-of-school)</option>
              <option>Disability status</option>
              <option>Age group (under 10 / 10–14 / 15–19)</option>
              <option>Activity type</option>
              <option>Objective</option>
            </select>
          </div>
          <svg width="100%" height="160" viewBox="0 0 260 150" xmlns="http://www.w3.org/2000/svg" style={{ display: 'block' }}>
            {/* Y-axis + gridlines */}
            <line x1="28" y1="8" x2="28" y2="118" stroke="#e2e8f0" strokeWidth="1"/>
            <line x1="28" y1="118" x2="255" y2="118" stroke="#e2e8f0" strokeWidth="1"/>
            {[{y:38,label:'40k'},{y:58,label:'30k'},{y:78,label:'20k'},{y:98,label:'10k'}].map(({y,label}) => (
              <g key={label}>
                <line x1="28" y1={y} x2="255" y2={y} stroke="#f1f5f9" strokeWidth="0.8" strokeDasharray="3,2"/>
                <text x="24" y={y+3} fontSize="7" fill="#94a3b8" textAnchor="end" fontFamily="sans-serif">{label}</text>
              </g>
            ))}
            {/* Stacked bars: F (dark blue, bottom) + M (light blue, on top) */}
            {STACKED_DATA.map((d, i) => {
              const maxVal = 50000;
              const chartH = 110; // usable height (y 8–118)
              const baseY = 118;
              const hF = Math.round((d.f / maxVal) * chartH);
              const hM = Math.round((d.m / maxVal) * chartH);
              const total = d.f + d.m;
              const hTotal = hF + hM;
              const barW = 28;
              const x = 38 + i * 44;
              const totalLabel = total >= 1000 ? `${(total/1000).toFixed(1).replace(/\.0$/,'')}k` : total;
              return (
                <g key={d.label}>
                  {/* Female — bottom */}
                  <rect x={x} y={baseY - hF} width={barW} height={hF} fill="#185FA5" rx="2"/>
                  {/* Male — stacked above */}
                  <rect x={x} y={baseY - hF - hM} width={barW} height={hM} fill="#85B7EB" rx="2"/>
                  {/* Total label on top */}
                  <text x={x + barW/2} y={baseY - hTotal - 3} fontSize="7.5" fill="#334155" textAnchor="middle" fontFamily="sans-serif" fontWeight="600">{totalLabel}</text>
                  {/* X-axis labels */}
                  <text x={x + barW/2} y="130" fontSize="7" fill="#94a3b8" textAnchor="middle" fontFamily="sans-serif">{d.label}</text>
                  <text x={x + barW/2} y="139" fontSize="6.5" fill="#94a3b8" textAnchor="middle" fontFamily="sans-serif">{d.sub}</text>
                </g>
              );
            })}
          </svg>
          <div style={{ display: 'flex', gap: 16, marginTop: 4 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 10, color: C.textSec }}>
              <div style={{ width: 10, height: 10, borderRadius: 2, background: '#185FA5' }} />Female
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 10, color: C.textSec }}>
              <div style={{ width: 10, height: 10, borderRadius: 2, background: '#85B7EB' }} />Male
            </div>
            <span style={{ marginLeft: 'auto', fontSize: 10, color: C.textMuted }}>Total: <strong style={{ color: C.text }}>48.3k</strong></span>
          </div>
        </Panel>

        {/* [R2 C2] Submission & verification status — two donuts */}
        <Panel title="Submission & verification status — Mar–Apr 2026">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            {/* Submission donut */}
            <div>
              <div style={{ fontSize: 10, fontWeight: 600, color: C.textSec, marginBottom: 8, textAlign: 'center' }}>Submission</div>
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 8 }}>
                <svg width="80" height="80" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="40" cy="40" r="30" fill="none" stroke="#e2e8f0" strokeWidth="11"/>
                  <circle cx="40" cy="40" r="30" fill="none" stroke="#185FA5" strokeWidth="11" strokeDasharray="135.1 188.5" strokeDashoffset="47" transform="rotate(-90 40 40)"/>
                  <circle cx="40" cy="40" r="30" fill="none" stroke="#EF9F27" strokeWidth="11" strokeDasharray="35.6 188.5" strokeDashoffset="-88.1" transform="rotate(-90 40 40)"/>
                  <circle cx="40" cy="40" r="30" fill="none" stroke="#E24B4A" strokeWidth="11" strokeDasharray="17.7 188.5" strokeDashoffset="-123.7" transform="rotate(-90 40 40)"/>
                  <text x="40" y="44" fontSize="13" fontWeight="700" fill="#1a1a2e" textAnchor="middle" fontFamily="sans-serif">72%</text>
                </svg>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {[['#185FA5','Submitted','38'],['#EF9F27','Draft','10'],['#E24B4A','Not submitted','5']].map(([color, label, n]) => (
                  <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, color: C.textSec }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0 }} />
                    <span style={{ flex: 1 }}>{label}</span><span style={{ fontWeight: 600, color: C.text }}>{n}</span>
                  </div>
                ))}
              </div>
            </div>
            {/* Verification donut */}
            <div>
              <div style={{ fontSize: 10, fontWeight: 600, color: C.textSec, marginBottom: 8, textAlign: 'center' }}>Verification</div>
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 8 }}>
                <svg width="80" height="80" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="40" cy="40" r="30" fill="none" stroke="#e2e8f0" strokeWidth="11"/>
                  <circle cx="40" cy="40" r="30" fill="none" stroke="#10b981" strokeWidth="11" strokeDasharray="94.2 188.5" strokeDashoffset="47" transform="rotate(-90 40 40)"/>
                  <circle cx="40" cy="40" r="30" fill="none" stroke="#85B7EB" strokeWidth="11" strokeDasharray="47.1 188.5" strokeDashoffset="-47.2" transform="rotate(-90 40 40)"/>
                  <circle cx="40" cy="40" r="30" fill="none" stroke="#e2e8f0" strokeWidth="11" strokeDasharray="47.2 188.5" strokeDashoffset="-94.3" transform="rotate(-90 40 40)"/>
                  <text x="40" y="44" fontSize="13" fontWeight="700" fill="#1a1a2e" textAnchor="middle" fontFamily="sans-serif">50%</text>
                </svg>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {[['#10b981','Verified','22'],['#85B7EB','Pending review','21'],['#e2e8f0','Not yet reviewed','18']].map(([color, label, n]) => (
                  <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, color: C.textSec }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0, border: color === '#e2e8f0' ? `1px solid ${C.border}` : 'none' }} />
                    <span style={{ flex: 1 }}>{label}</span><span style={{ fontWeight: 600, color: C.text }}>{n}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div style={{ fontSize: 10, color: C.textMuted, paddingTop: 10, borderTop: `1px solid ${C.borderLight}`, marginTop: 10 }}>
            Deadline: 30 June 2026 ·{' '}
            <span
              onClick={handleSendReminders}
              style={{ color: reminderState.loading ? C.textMuted : C.blue600, cursor: reminderState.loading ? 'default' : 'pointer' }}
            >
              {reminderState.loading ? 'Sending…' : reminderState.result ? reminderState.result.message : 'Send reminders to 18 →'}
            </span>
          </div>
        </Panel>
      </div>

      {/* Partners needing attention */}
      <div style={{ background: C.white, border: `1px solid ${C.border}`, borderRadius: 8, padding: '14px 16px' }}>
        <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 12, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          Partners needing attention
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 11, color: C.textSec }}>18 require action</span>
            <span onClick={() => setActivePage('directory')} style={{ fontSize: 11, color: C.blue600, cursor: 'pointer', fontWeight: 500 }}>Full directory →</span>
          </div>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 0, borderBottom: `1px solid ${C.border}`, marginBottom: 12 }}>
          {[
            { id: 'not-submitted', label: 'Not submitted', count: 7, color: C.red500, textColor: C.red900, countBg: C.redBg, countBorder: C.red100 },
            { id: 'draft', label: 'Draft', count: 11, color: C.amber400, textColor: C.amber600, countBg: '#f1f5f9', countBorder: C.border },
            { id: 'sla-pending', label: 'SLA pending', count: 13, color: C.blue600, textColor: C.blue900, countBg: '#f1f5f9', countBorder: C.border },
          ].map(tab => (
            <div key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
              padding: '6px 14px', fontSize: 11, fontWeight: 500, cursor: 'pointer',
              borderBottom: activeTab === tab.id ? `2px solid ${tab.color}` : '2px solid transparent',
              color: activeTab === tab.id ? tab.textColor : C.textSec,
              marginBottom: -1,
            }}>
              {tab.label}
              <span style={{ background: activeTab === tab.id ? tab.countBg : '#f1f5f9', color: activeTab === tab.id ? tab.textColor : C.textSec, border: `1px solid ${activeTab === tab.id ? tab.countBorder : C.border}`, borderRadius: 10, padding: '1px 6px', fontSize: 10, marginLeft: 4 }}>{tab.count}</span>
            </div>
          ))}
        </div>

        {/* Not submitted list */}
        {activeTab === 'not-submitted' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {ATTENTION.map(p => (
              <div key={p.name} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 10px', borderRadius: 6, background: C.redBg, border: `1px solid ${C.red100}` }}>
                <div>
                  <div style={{ fontSize: 11, fontWeight: 600, color: C.text }}>{p.name}</div>
                  <div style={{ fontSize: 10, color: C.textMuted, marginTop: 1 }}>{p.region} · {p.sla}</div>
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <span style={{ fontSize: 10, color: C.red900 }}>No submission</span>
                  <span style={{ fontSize: 11, color: C.red700, cursor: 'pointer', fontWeight: 500, whiteSpace: 'nowrap' }}>Send reminder</span>
                </div>
              </div>
            ))}
            <div style={{ textAlign: 'center', padding: '6px 0' }}>
              <span onClick={() => setActivePage('directory')} style={{ fontSize: 11, color: C.blue600, cursor: 'pointer', fontWeight: 500 }}>+ 4 more not submitted — view in directory →</span>
            </div>
            <div style={{ padding: '8px 10px', background: '#f8fafc', borderRadius: 6, border: `1px solid ${C.borderLight}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 11, color: C.textSec }}>
                {reminderState.result ? reminderState.result.message : 'Send bulk reminder to all 7 non-submitting partners'}
              </span>
              <button
                onClick={handleSendReminders}
                disabled={reminderState.loading}
                style={{ padding: '5px 12px', background: reminderState.loading ? C.textMuted : C.red500, color: C.white, border: 'none', borderRadius: 5, fontSize: 11, fontWeight: 500, cursor: reminderState.loading ? 'default' : 'pointer' }}
              >
                {reminderState.loading ? 'Sending…' : 'Send all →'}
              </button>
            </div>
          </div>
        )}

        {/* Draft list */}
        {activeTab === 'draft' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {DRAFTS.map(p => (
              <div key={p.name} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 10px', borderRadius: 6, background: C.amberBg, border: `1px solid ${C.amber100}` }}>
                <div>
                  <div style={{ fontSize: 11, fontWeight: 600, color: C.text }}>{p.name}</div>
                  <div style={{ fontSize: 10, color: C.textMuted, marginTop: 1 }}>{p.region} · Draft started {p.started}</div>
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <span style={{ fontSize: 10, color: C.amber600 }}>Deadline in {p.days} days</span>
                  <span style={{ fontSize: 11, color: C.amber700, cursor: 'pointer', fontWeight: 500 }}>Chase →</span>
                </div>
              </div>
            ))}
            <div style={{ textAlign: 'center', padding: '6px 0' }}>
              <span style={{ fontSize: 11, color: C.blue600, cursor: 'pointer', fontWeight: 500 }}>+ 9 more drafts — view in directory →</span>
            </div>
          </div>
        )}

        {/* SLA pending list */}
        {activeTab === 'sla-pending' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {[
              { name: 'Street Child of Sierra Leone', sent: '15 Mar', status: 'No response' },
              { name: 'FAWE Sierra Leone', sent: '20 Mar', status: 'No response' },
            ].map(p => (
              <div key={p.name} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 10px', borderRadius: 6, background: '#f8fafc', border: `1px solid ${C.border}` }}>
                <div>
                  <div style={{ fontSize: 11, fontWeight: 600, color: C.text }}>{p.name}</div>
                  <div style={{ fontSize: 10, color: C.textMuted, marginTop: 1 }}>SLA sent {p.sent} · {p.status}</div>
                </div>
                <span style={{ fontSize: 11, color: C.blue600, cursor: 'pointer', fontWeight: 500 }}>Follow up →</span>
              </div>
            ))}
            <div style={{ textAlign: 'center', padding: '6px 0' }}>
              <span style={{ fontSize: 11, color: C.blue600, cursor: 'pointer', fontWeight: 500 }}>+ 11 more SLAs pending — view in directory →</span>
            </div>
          </div>
        )}
      </div>

      <div style={{ position: 'fixed', bottom: 12, right: 14, fontSize: 10, color: C.textMuted, fontStyle: 'italic', pointerEvents: 'none' }}>
        Prototype v1.0 — MBSSE SRGBV Coordination Hub — May 2026
      </div>
    </main>
  );
}
