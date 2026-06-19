export const C = {
  // ── Sierra Leone Green (primary brand) ───────────────────────────────────
  blue900: '#0A5C1B',   // dark green — headers, badges, text-on-light-green
  blue700: '#14892A',   // medium-dark — button hover
  blue600: '#1EB53A',   // SL flag green — primary actions, active states
  blue400: '#46C75A',   // lighter green — hover accents
  blue200: '#8DD99D',   // light green — disabled / decorative
  blue100: '#BDE9C7',   // very light green — borders on tinted elements
  blueBg:  '#E6F7EA',   // near-white tint — hover / active backgrounds

  // ── Sierra Leone Blue (secondary accent) ─────────────────────────────────
  slBlue:      '#0072C6',
  slBlueBg:    '#E0EEFA',
  slBlueLight: '#B3D1F0',

  // ── Status: success ───────────────────────────────────────────────────────
  green900: '#27500A',
  green700: '#1A6B3C',
  green100: '#C0DD97',
  greenBg:  '#EAF3DE',

  // ── Status: warning ───────────────────────────────────────────────────────
  amber700: '#854F0B',
  amber600: '#633806',
  amber400: '#EF9F27',
  amber100: '#FAC775',
  amberBg:  '#FAEEDA',

  // ── Status: error ─────────────────────────────────────────────────────────
  red900: '#791F1F',
  red700: '#A32D2D',
  red500: '#E24B4A',
  red100: '#F7C1C1',
  redBg:  '#FCEBEB',

  // ── Neutrals ──────────────────────────────────────────────────────────────
  text:        '#1a1a2e',
  textSec:     '#64748b',
  textMuted:   '#94a3b8',
  border:      '#e2e8f0',
  borderLight: '#f1f5f9',
  bg:          '#f4f6f9',
  white:       '#ffffff',
};

export const pill = (variant) => {
  const map = {
    ok: { background: C.greenBg, color: C.green900, border: `1px solid ${C.green100}` },
    info: { background: C.blueBg, color: C.blue900, border: `1px solid ${C.blue100}` },
    warn: { background: C.amberBg, color: C.amber600, border: `1px solid ${C.amber100}` },
    err: { background: C.redBg, color: C.red900, border: `1px solid ${C.red100}` },
    grey: { background: C.borderLight, color: C.textSec, border: `1px solid ${C.border}` },
  };
  return {
    ...map[variant],
    fontSize: 10,
    padding: '2px 8px',
    borderRadius: 10,
    fontWeight: 500,
    display: 'inline-block',
    whiteSpace: 'nowrap',
  };
};

export const statusVariant = (status) => {
  if (status === 'Submitted' || status === 'Signed' || status === 'Active') return 'ok';
  if (status === 'Verified') return 'info';
  if (status === 'Draft' || status === 'Pending') return 'warn';
  if (status === 'Not submitted' || status === 'Closed') return 'err';
  return 'grey';
};

export const objColor = (obj) => {
  if (obj?.includes('1')) return { background: C.blueBg, color: C.blue900 };
  if (obj?.includes('2')) return { background: C.greenBg, color: C.green900 };
  if (obj?.includes('3')) return { background: C.amberBg, color: C.amber600 };
  return { background: C.borderLight, color: C.textSec };
};
