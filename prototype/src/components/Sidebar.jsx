import React from 'react';
import { C } from '../tokens.js';

// 'Home' is reached by clicking the SRGBV Coordination Hub title in the top nav.
const NAV = [
  { section: 'Main', items: ['Dashboard', 'Partner directory', 'Reporting form', 'GEM Report', 'Submissions'] },
  { section: 'Reports', items: ['Activity reports', 'Analytics', 'Export data'] },
  { section: 'Admin', items: ['User management', 'Form settings', 'System settings'] },
];

const PAGE_MAP = {
  'Home':             'partner-home', // overridden for gem_coordinator → 'gem-home' below
  'Dashboard':        'dashboard',
  'Partner directory': 'directory',
  'Reporting form':   'form',
  'Activity reports': 'reports',
  'Analytics':        'analytics',
  'Export data':      'export',
  'GEM Report':       'gem',
  'Submissions':      'submissions',
  'User management':  'users',
};

// Items visible to GEM coordinators
const GEM_ALLOWED = new Set(['Home', 'Dashboard', 'Analytics', 'GEM Report']);

export default function Sidebar({ activePage, setActivePage, user }) {
  const isAdmin   = user?.role === 'admin';
  const isViewer  = user?.role === 'viewer';
  const isGem     = user?.role === 'gem_coordinator';
  const isPartner = user?.role === 'partner';

  const resolvePageId = (item) => {
    if (item === 'Home') return isGem ? 'gem-home' : 'partner-home';
    return PAGE_MAP[item];
  };

  return (
    <aside style={{
      width: 178, background: C.white, borderRight: `1px solid ${C.border}`,
      padding: '14px 0', flexShrink: 0, position: 'sticky', top: 54,
      height: 'calc(100vh - 54px)', overflowY: 'auto',
    }}>
      {NAV.map(({ section, items }) => (
        <div key={section}>
          <div style={{
            fontSize: 10, fontWeight: 600, color: C.textMuted, textTransform: 'uppercase',
            letterSpacing: '.08em', padding: '10px 14px 5px',
          }}>{section}</div>
          {items.filter(item => {
            if (isGem) return GEM_ALLOWED.has(item);
            if (item === 'Home' && !isPartner) return false;
            if (item === 'GEM Report' && isPartner) return false;
            if (item === 'User management' && !isAdmin) return false;
            if (item === 'Reporting form' && isViewer) return false;
            if (item === 'GEM Report' && isViewer) return false;
            return true;
          }).map(item => {
            const pageId = resolvePageId(item);
            const isActive = pageId && activePage === pageId;
            return (
              <div key={item} onClick={() => pageId && setActivePage(pageId)} style={{
                display: 'flex', alignItems: 'center', gap: 9,
                padding: '7px 14px', fontSize: 12,
                color: isActive ? C.blue600 : C.textSec,
                cursor: pageId ? 'pointer' : 'default',
                borderLeft: `2px solid ${isActive ? C.blue600 : 'transparent'}`,
                background: isActive ? C.blueBg : 'transparent',
                fontWeight: isActive ? 500 : 400,
              }}>
                <div style={{ width: 5, height: 5, borderRadius: '50%', background: 'currentColor', flexShrink: 0 }} />
                {item}
              </div>
            );
          })}
        </div>
      ))}
    </aside>
  );
}
