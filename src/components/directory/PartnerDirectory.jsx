import React, { useState, useMemo } from 'react';
import { PARTNERS, STAT_SUMMARY, FOCUS_AREAS, OBJECTIVES, DISTRICTS } from '../../data/partners.js';
import { C, pill, statusVariant, objColor } from '../../tokens.js';
import PartnerDrawer from './PartnerDrawer.jsx';

const PARTNER_TYPES = ['INGO', 'Local NGO', 'UN Agency', 'Government', 'Academic'];

function StatCard({ val, label, sub, alert }) {
  return (
    <div style={{
      background: C.white, border: `1px solid ${C.border}`,
      borderLeft: alert ? `3px solid ${C.red500}` : `1px solid ${C.border}`,
      borderRadius: 8, padding: '12px 16px',
    }}>
      <div style={{ fontSize: 22, fontWeight: 600, color: alert ? C.red700 : C.text, lineHeight: 1 }}>{val}</div>
      <div style={{ fontSize: 11, color: C.textSec, marginTop: 4 }}>{label}</div>
      <div style={{ fontSize: 10, color: alert ? C.red700 : C.textMuted, marginTop: 2 }}>{sub}</div>
    </div>
  );
}

function ObjBadge({ obj }) {
  const style = objColor(obj);
  return (
    <span style={{
      ...style, fontSize: 9, padding: '2px 6px', borderRadius: 3,
      display: 'inline-block', marginRight: 3, marginBottom: 2,
    }}>{obj}</span>
  );
}

function FocusTag({ label }) {
  return (
    <span style={{
      fontSize: 9, padding: '2px 6px', borderRadius: 3,
      background: C.blueBg, color: C.blue900, border: `1px solid ${C.blue100}`,
      whiteSpace: 'nowrap',
    }}>{label}</span>
  );
}

export default function PartnerDirectory() {
  const [search, setSearch] = useState('');
  const [filterObj, setFilterObj] = useState('All objectives');
  const [filterFocus, setFilterFocus] = useState('All focus areas');
  const [filterDistrict, setFilterDistrict] = useState('All districts');
  const [filterStatus, setFilterStatus] = useState('All statuses');
  const [filterSla, setFilterSla] = useState('All SLA statuses');
  const [view, setView] = useState('table');
  const [expandedId, setExpandedId] = useState(null);
  const [drawerPartner, setDrawerPartner] = useState(null);
  const [sortCol, setSortCol] = useState('name');
  const [sortDir, setSortDir] = useState('asc');

  const filtered = useMemo(() => {
    let list = PARTNERS;
    if (search) list = list.filter(p => p.name.toLowerCase().includes(search.toLowerCase()) || p.focalPerson.toLowerCase().includes(search.toLowerCase()));
    if (filterObj !== 'All objectives') list = list.filter(p => p.objectives.some(o => o === filterObj));
    if (filterFocus !== 'All focus areas') list = list.filter(p => p.focusAreas.some(f => f.includes(filterFocus)));
    if (filterDistrict !== 'All districts') list = list.filter(p => p.districts.some(d => d.includes(filterDistrict)));
    if (filterStatus !== 'All statuses') list = list.filter(p => p.submissionStatus === filterStatus);
    if (filterSla !== 'All SLA statuses') list = list.filter(p => p.slaStatus === filterSla);

    list = [...list].sort((a, b) => {
      let av = sortCol === 'name' ? a.name : sortCol === 'status' ? a.submissionStatus : a.slaStatus;
      let bv = sortCol === 'name' ? b.name : sortCol === 'status' ? b.submissionStatus : b.slaStatus;
      return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
    });
    return list;
  }, [search, filterObj, filterFocus, filterDistrict, filterStatus, filterSla, sortCol, sortDir]);

  const handleSort = (col) => {
    if (sortCol === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortCol(col); setSortDir('asc'); }
  };

  const selW = { fontSize: 11, padding: '5px 9px', border: `1px solid ${C.border}`, borderRadius: 5, background: C.white, color: C.text, cursor: 'pointer' };
  const thStyle = (col) => ({
    textAlign: 'left', padding: '9px 14px', fontSize: 10, fontWeight: 600,
    color: sortCol === col ? C.blue600 : C.textSec,
    borderBottom: `1px solid ${C.border}`, whiteSpace: 'nowrap',
    background: '#f8fafc', cursor: 'pointer', userSelect: 'none',
  });
  const tdStyle = { padding: '10px 14px', borderBottom: `1px solid ${C.borderLight}`, verticalAlign: 'middle' };

  return (
    <main style={{ flex: 1, padding: '18px 20px', overflow: 'auto', minWidth: 0 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 3 }}>Partner Directory</div>
          <div style={{ fontSize: 11, color: C.textSec }}>All registered organisations — 61 active · Last updated 25 Apr 2026</div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button style={{ padding: '7px 12px', background: C.white, color: C.textSec, border: `1px solid ${C.border}`, borderRadius: 6, fontSize: 12, cursor: 'pointer' }}>↓ Export CSV</button>
          <button style={{ padding: '7px 16px', background: C.blue600, color: C.white, border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 500, cursor: 'pointer' }}>+ Add partner</button>
        </div>
      </div>

      {/* Stat strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12, marginBottom: 16 }}>
        <StatCard val={STAT_SUMMARY.total} label="Registered organisations" sub={`+${STAT_SUMMARY.newThisCycle} onboarded this cycle`} />
        <StatCard val={STAT_SUMMARY.submitted} label="Submitted this period" sub={`${STAT_SUMMARY.complianceRate}% compliance rate`} />
        <StatCard val={STAT_SUMMARY.slaSigned} label="SLAs signed" sub={`${STAT_SUMMARY.slaPending} pending signature`} />
        <StatCard val={STAT_SUMMARY.notSubmitted} label="Not yet submitted" sub="Deadline: 30 Jun 2026" alert />
      </div>

      {/* Toolbar */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 14, flexWrap: 'wrap', background: C.white, padding: '10px 14px', borderRadius: 8, border: `1px solid ${C.border}` }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '5px 10px', border: `1px solid ${C.border}`, borderRadius: 5, background: '#f8fafc', flex: 1, maxWidth: 260 }}>
          <span style={{ fontSize: 12, color: C.textMuted }}>🔍</span>
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search name, focal person..." style={{ border: 'none', background: 'transparent', fontSize: 11, color: C.textSec, outline: 'none', width: '100%' }} />
        </div>
        <span style={{ fontSize: 11, fontWeight: 600, color: C.textSec }}>Filter:</span>
        <select value={filterObj} onChange={e => setFilterObj(e.target.value)} style={selW}>
          <option>All objectives</option>
          {OBJECTIVES.map(o => <option key={o.short} value={o.short}>{o.full}</option>)}
        </select>
        <select value={filterFocus} onChange={e => setFilterFocus(e.target.value)} style={selW}>
          <option>All focus areas</option>
          {FOCUS_AREAS.map(f => <option key={f}>{f}</option>)}
        </select>
        <select value={filterDistrict} onChange={e => setFilterDistrict(e.target.value)} style={selW}>
          <option>All districts</option>
          {DISTRICTS.map(d => <option key={d}>{d}</option>)}
        </select>
        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} style={selW}>
          <option>All statuses</option>
          {['Submitted', 'Verified', 'Draft', 'Not submitted'].map(s => <option key={s}>{s}</option>)}
        </select>
        <select value={filterSla} onChange={e => setFilterSla(e.target.value)} style={selW}>
          <option>All SLA statuses</option>
          {['Signed', 'Pending'].map(s => <option key={s}>{s}</option>)}
        </select>
        <button onClick={() => { setSearch(''); setFilterObj('All objectives'); setFilterFocus('All focus areas'); setFilterDistrict('All districts'); setFilterStatus('All statuses'); setFilterSla('All SLA statuses'); }} style={{ fontSize: 11, padding: '5px 10px', borderRadius: 5, background: 'transparent', color: C.textSec, border: `1px solid ${C.border}`, cursor: 'pointer' }}>Reset</button>
        <span style={{ fontSize: 11, color: C.textMuted, marginLeft: 'auto' }}>Showing {filtered.length} of {STAT_SUMMARY.total} organisations</span>
        <div style={{ display: 'flex', border: `1px solid ${C.border}`, borderRadius: 6, overflow: 'hidden', marginLeft: 8 }}>
          {['table', 'cards'].map(v => (
            <button key={v} onClick={() => setView(v)} style={{
              padding: '5px 10px', fontSize: 11, border: 'none', cursor: 'pointer',
              background: view === v ? C.blueBg : C.white, color: view === v ? C.blue600 : C.textSec, fontWeight: view === v ? 500 : 400,
            }}>{v === 'table' ? '☰ Table' : '⊞ Cards'}</button>
          ))}
        </div>
      </div>

      {/* TABLE VIEW */}
      {view === 'table' && (
        <div style={{ background: C.white, border: `1px solid ${C.border}`, borderRadius: 8, overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
              <thead>
                <tr>
                  <th onClick={() => handleSort('name')} style={thStyle('name')}>Organisation {sortCol === 'name' ? (sortDir === 'asc' ? '↓' : '↑') : '↕'}</th>
                  <th style={{ ...thStyle(), cursor: 'default' }}>Type</th>
                  <th style={{ ...thStyle(), cursor: 'default' }}>Objective(s)</th>
                  <th style={{ ...thStyle(), cursor: 'default' }}>Focus area(s)</th>
                  <th style={{ ...thStyle(), cursor: 'default' }}>Districts</th>
                  <th style={{ ...thStyle(), cursor: 'default' }}>Proj.</th>
                  <th onClick={() => handleSort('sla')} style={thStyle('sla')}>SLA {sortCol === 'sla' ? (sortDir === 'asc' ? '↓' : '↑') : '↕'}</th>
                  <th onClick={() => handleSort('status')} style={thStyle('status')}>Submission {sortCol === 'status' ? (sortDir === 'asc' ? '↓' : '↑') : '↕'}</th>
                  <th style={{ ...thStyle(), cursor: 'default' }}>Last submitted</th>
                  <th style={{ ...thStyle(), cursor: 'default' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(p => {
                  const isExpanded = expandedId === p.id;
                  const notSubmitted = p.submissionStatus === 'Not submitted';
                  const isDraft = p.submissionStatus === 'Draft';
                  return (
                    <React.Fragment key={p.id}>
                      <tr onClick={() => setExpandedId(isExpanded ? null : p.id)} style={{ cursor: 'pointer', background: isExpanded ? C.blueBg : 'transparent' }}>
                        <td style={tdStyle}>
                          <div style={{ fontWeight: 600, color: C.text, fontSize: 12 }}>{p.name}</div>
                          <div style={{ fontSize: 10, padding: '1px 6px', background: C.borderLight, borderRadius: 3, display: 'inline-block', marginTop: 2, color: C.textSec }}>{p.projects} project{p.projects !== 1 ? 's' : ''}</div>
                        </td>
                        <td style={tdStyle}><span style={{ fontSize: 10, color: C.textSec }}>{p.type}</span></td>
                        <td style={tdStyle}>{p.objectives.map(o => <ObjBadge key={o} obj={o} />)}</td>
                        <td style={tdStyle}>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
                            {p.focusAreas.slice(0, 3).map(f => <FocusTag key={f} label={f} />)}
                            {p.focusAreas.length > 3 && <span style={{ fontSize: 10, color: C.textMuted }}>+{p.focusAreas.length - 3}</span>}
                          </div>
                        </td>
                        <td style={tdStyle}>
                          <span style={{ fontSize: 10, color: C.textSec }}>{p.districts.slice(0, 3).join(', ')}</span>
                          {p.districts.length > 3 && <span style={{ fontSize: 10, color: C.textMuted }}> +{p.districts.length - 3}</span>}
                        </td>
                        <td style={{ ...tdStyle, textAlign: 'center', fontSize: 11, color: C.textSec }}>{p.projects}</td>
                        <td style={tdStyle}><span style={pill(statusVariant(p.slaStatus))}>{p.slaStatus}</span></td>
                        <td style={tdStyle}><span style={pill(statusVariant(p.submissionStatus))}>{p.submissionStatus}</span></td>
                        <td style={{ ...tdStyle, fontSize: 11, color: p.lastSubmitted ? C.textSec : C.textMuted }}>{p.lastSubmitted || '—'}</td>
                        <td style={tdStyle} onClick={e => e.stopPropagation()}>
                          <div style={{ display: 'flex', gap: 8 }}>
                            <span onClick={() => setDrawerPartner(p)} style={{ fontSize: 11, color: C.blue600, cursor: 'pointer', fontWeight: 500, whiteSpace: 'nowrap' }}>View →</span>
                            {notSubmitted && <span style={{ fontSize: 11, color: C.red700, cursor: 'pointer', fontWeight: 500, whiteSpace: 'nowrap' }}>Send reminder</span>}
                            {isDraft && <span style={{ fontSize: 11, color: C.amber700, cursor: 'pointer', fontWeight: 500 }}>Chase</span>}
                            {!notSubmitted && !isDraft && <span style={{ fontSize: 11, color: C.blue600, cursor: 'pointer', fontWeight: 500 }}>Edit</span>}
                          </div>
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr>
                          <td colSpan={10} style={{ padding: 0 }}>
                            <ExpandedRow partner={p} onViewDrawer={() => setDrawerPartner(p)} />
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
                {filtered.length === 0 && (
                  <tr><td colSpan={10} style={{ textAlign: 'center', padding: '32px 0', color: C.textMuted, fontSize: 12 }}>No organisations match the current filters</td></tr>
                )}
              </tbody>
            </table>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', borderTop: `1px solid ${C.borderLight}`, background: C.white }}>
            <span style={{ fontSize: 11, color: C.textMuted }}>Showing {filtered.length} of {STAT_SUMMARY.total} organisations</span>
            <div style={{ display: 'flex', gap: 4 }}>
              {[1, 2, 3, '…', 9].map((p, i) => (
                <button key={i} style={{
                  padding: '4px 10px', border: `1px solid ${C.border}`, borderRadius: 4, fontSize: 11,
                  background: p === 1 ? C.blueBg : C.white, color: p === 1 ? C.blue600 : C.textSec,
                  cursor: 'pointer', fontWeight: p === 1 ? 500 : 400,
                }}>{p}</button>
              ))}
              <button style={{ padding: '4px 10px', border: `1px solid ${C.border}`, borderRadius: 4, fontSize: 11, background: C.white, color: C.textSec, cursor: 'pointer' }}>Next →</button>
            </div>
          </div>
        </div>
      )}

      {/* CARD VIEW */}
      {view === 'cards' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14 }}>
          {filtered.map(p => (
            <OrgCard key={p.id} partner={p} onView={() => setDrawerPartner(p)} />
          ))}
        </div>
      )}

      {/* DRAWER */}
      {drawerPartner && <PartnerDrawer partner={drawerPartner} onClose={() => setDrawerPartner(null)} />}

      <div style={{ position: 'fixed', bottom: 12, right: 14, fontSize: 10, color: C.textMuted, fontStyle: 'italic', pointerEvents: 'none' }}>
        Prototype v1.0 — MBSSE School Safety Coordination Hub — May 2026
      </div>
    </main>
  );
}

function ExpandedRow({ partner: p, onViewDrawer }) {
  return (
    <div style={{ background: C.blueBg, borderTop: `1px solid ${C.blue100}` }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 0, padding: '14px 16px', borderBottom: `1px solid ${C.blue100}` }}>
        {[
          { label: 'Focal person', val: p.focalPerson },
          { label: 'Email', val: p.email },
          { label: 'Funding source', val: p.fundingSource },
          { label: 'Govt. counterpart', val: p.govCounterpart },
          { label: 'Total budget', val: p.totalBudget },
          { label: 'Project period', val: p.projectPeriod },
          { label: 'Schools reached', val: p.schoolsReached || '—' },
          { label: 'Beneficiaries', val: p.beneficiaries || '—' },
        ].reduce((pairs, item, i) => {
          if (i % 2 === 0) pairs.push([item]);
          else pairs[pairs.length - 1].push(item);
          return pairs;
        }, []).map((pair, colIdx) => (
          <div key={colIdx} style={{ padding: '0 16px', borderRight: colIdx < 3 ? `1px solid ${C.blue100}` : 'none', paddingLeft: colIdx === 0 ? 0 : 16 }}>
            {pair.map(({ label, val }) => (
              <div key={label} style={{ marginBottom: 8 }}>
                <div style={{ fontSize: 10, color: C.textSec, fontWeight: 500, marginBottom: 2 }}>{label}</div>
                <div style={{ fontSize: 11, color: C.text }}>{val}</div>
              </div>
            ))}
          </div>
        ))}
      </div>
      <div style={{ padding: '12px 16px' }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: C.blue600, marginBottom: 8 }}>Projects ({p.projects})</div>
        {p.projectList.slice(0, 2).map((proj, i) => (
          <div key={i} style={{ background: C.white, border: `1px solid ${C.blue100}`, borderRadius: 6, padding: '10px 12px', marginBottom: 6 }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: C.text, marginBottom: 5 }}>{proj.title}</div>
            <div style={{ display: 'flex', gap: 12, fontSize: 10, color: C.textSec, flexWrap: 'wrap', alignItems: 'center' }}>
              <span style={{ ...objColor(proj.obj), fontSize: 9, padding: '2px 6px', borderRadius: 3 }}>{proj.obj}</span>
              <span>🌍 {proj.districts}</span>
              <span>📅 {proj.period}</span>
              <span>💵 {proj.budget}</span>
              <span style={pill(statusVariant(proj.status))}>{proj.status}</span>
            </div>
          </div>
        ))}
        {p.projectList.length > 2 && (
          <div style={{ fontSize: 10, color: C.blue600, cursor: 'pointer', paddingTop: 4 }} onClick={onViewDrawer}>
            + {p.projectList.length - 2} more projects →
          </div>
        )}
      </div>
    </div>
  );
}

function OrgCard({ partner: p, onView }) {
  const initials = p.name.split(' ').slice(0, 2).map(w => w[0]).join('');
  const avatarColor = p.submissionStatus === 'Not submitted' ? { background: C.redBg, color: C.red700 }
    : p.submissionStatus === 'Draft' ? { background: C.amberBg, color: C.amber600 }
    : { background: C.blueBg, color: C.blue600 };

  return (
    <div onClick={onView} style={{
      background: C.white, border: `1px solid ${C.border}`, borderRadius: 8,
      padding: 16, cursor: 'pointer', transition: 'box-shadow .15s',
    }}
      onMouseEnter={e => e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,.08)'}
      onMouseLeave={e => e.currentTarget.style.boxShadow = 'none'}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 10 }}>
        <div>
          <div style={{ fontSize: 12, fontWeight: 600, color: C.text, marginBottom: 2 }}>{p.name}</div>
          <div style={{ fontSize: 10, color: C.textMuted }}>{p.type} · {p.projects} project{p.projects !== 1 ? 's' : ''}</div>
        </div>
        <div style={{ width: 36, height: 36, borderRadius: 8, ...avatarColor, fontSize: 13, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{initials}</div>
      </div>
      <div style={{ display: 'flex', gap: 3, flexWrap: 'wrap', marginBottom: 8 }}>
        {p.objectives.map(o => <ObjBadge key={o} obj={o} />)}
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3, marginBottom: 8 }}>
        {p.focusAreas.map(f => <FocusTag key={f} label={f} />)}
      </div>
      <div style={{ fontSize: 10, color: C.textSec, lineHeight: 1.5, marginBottom: 10 }}>
        {p.districts.slice(0, 3).join(', ')}{p.districts.length > 3 ? ` +${p.districts.length - 3}` : ''} · Focal: {p.focalPerson}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: 8, borderTop: `1px solid ${C.borderLight}` }}>
        <span style={pill(statusVariant(p.submissionStatus))}>{p.submissionStatus}</span>
        <span style={{ fontSize: 10, color: C.textMuted }}>{p.lastSubmitted || '—'}</span>
      </div>
    </div>
  );
}
