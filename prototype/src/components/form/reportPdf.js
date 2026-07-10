// Client-side "download my completed report" — renders the current form data as a
// clean, print-ready HTML document and opens the browser print dialog so the
// partner can Save as PDF. No external dependencies; produces selectable text.

const IND_LABELS = {
  schools_pre_primary: 'Schools reached — Pre-primary',
  schools_primary: 'Schools reached — Primary',
  schools_jss: 'Schools reached — Junior Secondary (JSS)',
  schools_sss: 'Schools reached — Senior Secondary (SSS)',
  schools_with_focal_person: 'Schools w/ trained SRGBV focal person',
  schools_with_reporting_protocol: 'Schools w/ SRGBV reporting protocol',
  schools_with_referral_pathway: 'Schools w/ SRGBV referral pathway',
  schools_held_schoolwide_campaign: 'Schools w/ school-wide SRGBV campaign',
  schools_held_peer_led_session: 'Schools w/ peer-led SRGBV session',
  schools_with_safe_space: 'Schools w/ designated safe space',
  students_inschool_f: 'In-school students — Female',
  students_inschool_m: 'In-school students — Male',
  students_inschool_age_under10: 'In-school — Age under 10',
  students_inschool_age_10_14: 'In-school — Age 10–14',
  students_inschool_age_15_19: 'In-school — Age 15–19',
  students_inschool_age_19_plus: 'In-school — 19 and older',
  students_oos_f: 'Out-of-school students — Female',
  students_oos_m: 'Out-of-school students — Male',
  students_oos_age_10_14: 'Out-of-school — Age 10–14',
  students_oos_age_15_19: 'Out-of-school — Age 15–19',
  students_oos_age_19_plus: 'Out-of-school — 19 and older',
  students_disability_f: 'Students w/ disability — Female',
  students_disability_m: 'Students w/ disability — Male',
  pregnant_girls: 'Pregnant girls reached',
  teenage_mothers: 'Teenage mothers reached',
  teenage_fathers: 'Teenage fathers reached',
  students_used_reporting_mechanism: 'Students who used reporting mechanism',
  students_confident_reporting: 'Students confident using reporting mechanism',
  teachers_demonstrated_grp: 'Teachers demonstrating GRP',
  community_members_f: 'Community members reached — Female',
  community_members_m: 'Community members reached — Male',
  community_sessions: 'Community sessions held',
  policy_dialogue_events: 'Policy dialogue events',
};

const CADRE_LABELS = {
  teacher: 'Teachers / school staff',
  district_official: 'District officials',
  central_official: 'Central officials',
};

const esc = (v) => String(v ?? '')
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;');

const stripNum = (s) => (s || '').replace(/^\s*\d+\.\s*/, '');

function field(label, value) {
  const v = (value == null || value === '') ? '—' : value;
  return `<tr><th>${esc(label)}</th><td>${esc(v)}</td></tr>`;
}

function longField(label, value) {
  if (!value) return '';
  return `<div class="long"><div class="ll">${esc(label)}</div><div class="lv">${esc(value)}</div></div>`;
}

function activityBlock(a, idx) {
  const dists = (a.districts && a.districts.length) ? a.districts : [''];
  let indHtml = '';
  dists.forEach(d => {
    const ind = a.ind?.[d] || {};
    const rows = Object.keys(IND_LABELS)
      .filter(k => Number(ind[k]) > 0)
      .map(k => `<tr><th>${esc(IND_LABELS[k])}</th><td>${esc(ind[k])}</td></tr>`)
      .join('');
    // training for this district
    const tr = a.training?.[d] || {};
    const trainRows = [];
    Object.keys(tr).forEach(fa => {
      Object.keys(CADRE_LABELS).forEach(cadre => {
        const f = Number(tr[fa]?.[`${cadre}_f`]) || 0;
        const m = Number(tr[fa]?.[`${cadre}_m`]) || 0;
        if (f || m) {
          trainRows.push(`<tr><th>${esc(CADRE_LABELS[cadre])} trained — ${esc(stripNum(fa))}</th><td>F: ${f} · M: ${m}</td></tr>`);
        }
      });
    });
    if (rows || trainRows.length) {
      indHtml += `<div class="dist"><div class="dh">${esc(d || 'District not specified')}</div>`
        + `<table class="kv">${rows}${trainRows.join('')}</table></div>`;
    }
  });
  if (!indHtml) indHtml = '<div class="muted">No indicator values entered.</div>';

  return `
  <div class="activity">
    <h3>Activity ${idx + 1}${a.activityTitle ? ' — ' + esc(a.activityTitle) : ''}</h3>
    <table class="kv">
      ${field('Focus area(s)', (a.focusAreas || []).map(stripNum).join(', '))}
      ${a.focusAreas?.includes('8. Other') && a.focusAreaOther ? field('Other focus area', a.focusAreaOther) : ''}
      ${field('Objectives', (a.objectives || []).join('; '))}
      ${field('Tactics', (a.tactics || []).join('; '))}
      ${field('District(s)', (a.districts || []).join(', '))}
      ${field('Activity type', a.activityType)}
      ${field('Intervention level(s)', (a.interventionLevels || []).join(', '))}
      ${field('Implementation status', a.implementationStatus)}
      ${field('Start date', a.startDate)}
      ${field('End date', a.endDate)}
    </table>
    ${longField('Description', a.description)}
    ${longField('Planned vs actual', a.plannedVsActual)}
    <div class="ind-title">Output indicators</div>
    ${indHtml}
  </div>`;
}

export function downloadReportPdf({ user, periodLabel, form, activities }) {
  const acts = (activities || []).map((a, i) => activityBlock(a, i)).join('');
  const generated = new Date().toLocaleString();

  const html = `<!DOCTYPE html><html><head><meta charset="utf-8">
  <title>SRGBV Report — ${esc(user?.org_name || 'Organisation')}</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
           color: #1f2937; margin: 32px; font-size: 12px; line-height: 1.5; }
    h1 { font-size: 18px; margin: 0 0 2px; }
    h2 { font-size: 13px; margin: 22px 0 6px; padding-bottom: 4px;
         border-bottom: 2px solid #1d4ed8; color: #1d4ed8; text-transform: uppercase; letter-spacing: .04em; }
    h3 { font-size: 12px; margin: 12px 0 6px; color: #111827; }
    .sub { color: #6b7280; font-size: 11px; margin-bottom: 2px; }
    table.kv { width: 100%; border-collapse: collapse; margin: 4px 0; }
    table.kv th { text-align: left; width: 45%; font-weight: 600; color: #374151;
                  border-bottom: 1px solid #eee; padding: 3px 8px 3px 0; vertical-align: top; }
    table.kv td { border-bottom: 1px solid #eee; padding: 3px 0; vertical-align: top; }
    .long { margin: 6px 0; }
    .long .ll { font-weight: 600; color: #374151; }
    .long .lv { white-space: pre-wrap; }
    .activity { border: 1px solid #e5e7eb; border-radius: 6px; padding: 10px 14px; margin: 10px 0;
                page-break-inside: avoid; }
    .ind-title { font-weight: 600; margin: 10px 0 4px; color: #1d4ed8; }
    .dist { margin: 6px 0; }
    .dist .dh { font-weight: 600; font-size: 11px; color: #111827; background: #f3f4f6;
                padding: 2px 8px; border-radius: 3px; display: inline-block; }
    .muted { color: #9ca3af; font-style: italic; }
    @media print { body { margin: 12mm; } h2 { page-break-after: avoid; } }
  </style></head><body>
    <h1>School Safety Coordination Hub — Partner Report</h1>
    <div class="sub">${esc(user?.org_name || 'Organisation')} · Reporting period: ${esc(periodLabel || '—')}</div>
    <div class="sub">Submitted by: ${esc(user?.full_name || user?.email || '—')} · Generated: ${esc(generated)}</div>

    <h2>Coverage</h2>
    <table class="kv">
      ${field('Project', form.project)}
      ${field('District(s)', (form.districts || []).join(', '))}
      ${field('Chiefdom(s)', (form.chiefdoms || []).join(', '))}
      ${field('Communities / towns', form.community)}
    </table>

    <h2>Activities &amp; output indicators</h2>
    ${acts || '<div class="muted">No activities entered.</div>'}

    <h2>Results &amp; outcomes</h2>
    ${longField('Key results', form.keyResults) || '<div class="muted">—</div>'}
    ${longField('Observed changes', form.observedChanges)}
    ${longField('Early outcomes', form.earlyOutcomes)}

    <h2>Budget &amp; coordination</h2>
    <table class="kv">
      ${field('Expenditure this period', form.expenditure ? `${form.expenditure} ${form.currency || ''}`.trim() : '')}
      ${field('Budget utilisation', form.budgetStatus)}
      ${field('Government engaged', form.govEngaged)}
      ${field('Government counterpart', form.govCounterpart)}
      ${field('Coordination meetings attended', form.coordinationMeetings)}
      ${field('Key partners', form.keyPartners)}
    </table>

    <h2>Challenges &amp; risks</h2>
    ${longField('Challenges', form.challenges)}
    ${longField('Risks', form.risks)}
    ${longField('Mitigations', form.mitigations)}

    <h2>Safeguarding</h2>
    <table class="kv">
      ${field('Safeguarding cases this period', form.safeguardingCases)}
      ${field('Number of cases reported', form.numCases)}
    </table>
    ${longField('Referral pathway', form.referralPathway)}
    ${longField('Action taken', form.actionTaken)}

    <h2>Looking ahead</h2>
    ${longField('Planned activities', form.plannedActivities)}
    ${longField('Support needed', form.supportNeeded)}
  </body></html>`;

  const w = window.open('', '_blank');
  if (!w) {
    alert('Please allow pop-ups to download your report as a PDF.');
    return;
  }
  w.document.open();
  w.document.write(html);
  w.document.close();
  w.focus();
  const doPrint = () => { try { w.print(); } catch (e) { /* user can print manually */ } };
  // Print once the new window has laid out its content.
  if (w.document.readyState === 'complete') setTimeout(doPrint, 300);
  else w.onload = () => setTimeout(doPrint, 300);
}
