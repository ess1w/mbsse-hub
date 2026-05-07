import React from 'react';
import { C } from '../tokens.js';

const NAV = [
  { section: 'Main', items: ['Dashboard', 'Coverage map', 'Partner directory', 'Submissions'] },
  { section: 'Reports', items: ['Activity reports', 'Export data'] },
  { section: 'Admin', items: ['User management', 'Form settings', 'System settings'] },
];

const PAGE_MAP = {
  'Dashboard': 'dashboard',
  'Partner directory': 'directory',
  'Activity reports': 'form',
};

export default function Sidebar({ activePage, setActivePage }) {
  return (
    <aside style={{
      width: 178, background: C.white, borderRight: `1px solid ${C.border}`,
      padding: '14px 0', flexShrink: 0, position: 'sticky', top: 48,
      height: 'calc(100vh - 48px)', overflowY: 'auto',
    }}>
      {NAV.map(({ section, items }) => (
        <div key={section}>
          <div style={{
            fontSize: 10, fontWeight: 600, color: C.textMuted, textTransform: 'uppercase',
            letterSpacing: '.08em', padding: '10px 14px 5px',
          }}>{section}</div>
          {items.map(item => {
            const pageId = PAGE_MAP[item];
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
