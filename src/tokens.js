export const C = {
  blue900: '#0C447C',
  blue700: '#185FA5',
  blue600: '#1F5C99',
  blue400: '#378ADD',
  blue200: '#85B7EB',
  blue100: '#B5D4F4',
  blueBg: '#EBF3FB',
  green900: '#27500A',
  green700: '#1A6B3C',
  green100: '#C0DD97',
  greenBg: '#EAF3DE',
  amber700: '#854F0B',
  amber600: '#633806',
  amber400: '#EF9F27',
  amber100: '#FAC775',
  amberBg: '#FAEEDA',
  red900: '#791F1F',
  red700: '#A32D2D',
  red500: '#E24B4A',
  red100: '#F7C1C1',
  redBg: '#FCEBEB',
  text: '#1a1a2e',
  textSec: '#64748b',
  textMuted: '#94a3b8',
  border: '#e2e8f0',
  borderLight: '#f1f5f9',
  bg: '#f4f6f9',
  white: '#fff',
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
