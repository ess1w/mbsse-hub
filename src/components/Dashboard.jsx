import React from 'react';
import { C, pill, statusVariant } from '../tokens.js';

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

  return (
    <main style={{ flex: 1, padding: '18px 20px', overflow: 'auto' }}>
      <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 3 }}>Dashboard</div>
      <div style={{ fontSize: 11, color: C.textSec, marginBottom: 16 }}>School Safety Coordination Hub — Last updated: 25 April 2026</div>

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

      {/* KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,minmax(0,1fr))', gap: 12, marginBottom: 16 }}>
        <KPI label="Reporting partners" val="61" sub="+5 onboarded this cycle" subColor={C.green700} />
        <KPI label="Schools reached" val="842" sub="Across 14 districts" />
        <KPI label="Beneficiaries this period" val="48,310" sub="58% female | 42% male" />
        <KPI label="Active districts" val="14 / 16" sub="2 with no coverage" />
        <KPI label="Reporting compliance" val="71%" sub="18 partners not submitted" alert />
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

      {/* Row: Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 14, marginBottom: 14 }}>
        {/* Activities by focus area */}
        <Panel title="Activities by focus area">
          <div style={{ background: '#f8fafc', borderRadius: 6, height: 140, border: `1px solid ${C.border}`, display: 'flex', alignItems: 'flex-end', padding: '10px 8px 0', overflow: 'hidden' }}>
            {bars.map((b, i) => (
              <div key={b.label} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%', justifyContent: 'flex-end' }}>
                <div title={`${b.label}: ${b.val}`} style={{ width: '80%', height: `${b.h}%`, background: barColors[i], borderRadius: '3px 3px 0 0' }} />
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-around', paddingTop: 4 }}>
            {bars.map(b => <span key={b.label} style={{ fontSize: 9, color: C.textMuted, textAlign: 'center', flex: 1 }}>{b.label}</span>)}
          </div>
        </Panel>

        {/* Activities by objective */}
        <Panel title="Activities by objective" annotation="Strategic view">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, paddingTop: 4 }}>
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
          <div style={{ marginTop: 10, paddingTop: 8, borderTop: `1px solid ${C.borderLight}`, fontSize: 10, color: C.textMuted }}>
            622 activities total · <span style={{ color: C.blue600, cursor: 'pointer' }}>View by tactic →</span>
          </div>
        </Panel>

        {/* Beneficiaries over time */}
        <Panel title="Beneficiaries over time" annotation="6-month">
          <svg width="100%" height="140" viewBox="0 0 220 130" xmlns="http://www.w3.org/2000/svg" style={{ display: 'block' }}>
            <line x1="22" y1="8" x2="22" y2="112" stroke="#e2e8f0" strokeWidth="1"/>
            <line x1="22" y1="112" x2="215" y2="112" stroke="#e2e8f0" strokeWidth="1"/>
            <line x1="22" y1="28" x2="215" y2="28" stroke="#f1f5f9" strokeWidth="0.8" strokeDasharray="3,2"/>
            <line x1="22" y1="58" x2="215" y2="58" stroke="#f1f5f9" strokeWidth="0.8" strokeDasharray="3,2"/>
            <line x1="22" y1="85" x2="215" y2="85" stroke="#f1f5f9" strokeWidth="0.8" strokeDasharray="3,2"/>
            <text x="18" y="31" fontSize="7" fill="#94a3b8" textAnchor="end" fontFamily="sans-serif">50k</text>
            <text x="18" y="61" fontSize="7" fill="#94a3b8" textAnchor="end" fontFamily="sans-serif">30k</text>
            <text x="18" y="88" fontSize="7" fill="#94a3b8" textAnchor="end" fontFamily="sans-serif">15k</text>
            <polyline points="27,102 65,90 103,75 141,57 179,42 215,30" fill="none" stroke="#185FA5" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round"/>
            <polyline points="27,106 65,98 103,89 141,74 179,63 215,55" fill="none" stroke="#9FE1CB" strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" strokeDasharray="4,2"/>
            {[27,65,103,141,179,215].map((x, i) => {
              const ys = [102,90,75,57,42,30];
              return <circle key={x} cx={x} cy={ys[i]} r="3" fill="#185FA5"/>;
            })}
            {['Jul 25','Sep 25','Nov 25','Jan 26','Mar 26'].map((label, i) => (
              <text key={label} x={27+i*38} y="124" fontSize="7" fill="#94a3b8" textAnchor="middle" fontFamily="sans-serif">{label}</text>
            ))}
            <text x="215" y="124" fontSize="7.5" fill="#185FA5" textAnchor="middle" fontFamily="sans-serif" fontWeight="600">48.3k</text>
          </svg>
          <div style={{ display: 'flex', gap: 12, marginTop: 4 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 10, color: C.textSec }}>
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#185FA5' }} />Total
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 10, color: C.textSec }}>
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#9FE1CB' }} />Female
            </div>
          </div>
        </Panel>

        {/* Submission status donut */}
        <Panel title="Submission status — Mar–Apr 2026">
          <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 10 }}>
            <svg width="92" height="92" viewBox="0 0 92 92" xmlns="http://www.w3.org/2000/svg">
              <circle cx="46" cy="46" r="35" fill="none" stroke="#e2e8f0" strokeWidth="13"/>
              <circle cx="46" cy="46" r="35" fill="none" stroke="#185FA5" strokeWidth="13" strokeDasharray="138 219.9" strokeDashoffset="55" transform="rotate(-90 46 46)"/>
              <circle cx="46" cy="46" r="35" fill="none" stroke="#EF9F27" strokeWidth="13" strokeDasharray="43.9 219.9" strokeDashoffset="-83" transform="rotate(-90 46 46)"/>
              <circle cx="46" cy="46" r="35" fill="none" stroke="#E24B4A" strokeWidth="13" strokeDasharray="37.9 219.9" strokeDashoffset="-126.9" transform="rotate(-90 46 46)"/>
              <text x="46" y="50" fontSize="15" fontWeight="600" fill="#1a1a2e" textAnchor="middle" fontFamily="sans-serif">71%</text>
            </svg>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {[['#185FA5','Submitted (43)'],['#EF9F27','Draft (11)'],['#E24B4A','Not submitted (7)']].map(([color, label]) => (
                <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: C.textSec }}>
                  <div style={{ width: 10, height: 10, borderRadius: '50%', background: color, flexShrink: 0 }} />
                  {label}
                </div>
              ))}
            </div>
          </div>
          <div style={{ fontSize: 10, color: C.textMuted, paddingTop: 8, borderTop: `1px solid ${C.borderLight}` }}>
            Deadline: 30 June 2026 · <span style={{ color: C.blue600, cursor: 'pointer' }}>Send reminders to 18 →</span>
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
              <span style={{ fontSize: 11, color: C.textSec }}>Send bulk reminder to all 7 non-submitting partners</span>
              <button style={{ padding: '5px 12px', background: C.red500, color: C.white, border: 'none', borderRadius: 5, fontSize: 11, fontWeight: 500, cursor: 'pointer' }}>Send all →</button>
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
        Prototype v1.0 — MBSSE School Safety Coordination Hub — May 2026
      </div>
    </main>
  );
}
