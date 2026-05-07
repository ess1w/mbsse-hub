import React from 'react';
import { C } from '../tokens.js';

export default function TopNav({ activePage, setActivePage }) {
  const nav = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'directory', label: 'Partner Directory' },
    { id: 'form', label: 'Activity Report' },
  ];

  return (
    <nav style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 20px', height: 48, background: C.white,
      borderBottom: `1px solid ${C.border}`, position: 'sticky', top: 0, zIndex: 100,
      boxShadow: '0 1px 3px rgba(0,0,0,.06)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          background: C.blue600, color: C.white, fontSize: 11, fontWeight: 600,
          padding: '4px 10px', borderRadius: 4,
        }}>MBSSE</div>
        <span style={{ fontSize: 13, fontWeight: 500 }}>School Safety Coordination Hub</span>
        <span style={{ fontSize: 11, color: C.textMuted, marginLeft: 2 }}>— Prototype</span>
        <div style={{ display: 'flex', gap: 4, marginLeft: 16 }}>
          {nav.map(n => (
            <button key={n.id} onClick={() => setActivePage(n.id)} style={{
              padding: '4px 12px', fontSize: 11, border: 'none', borderRadius: 4,
              cursor: 'pointer', fontWeight: activePage === n.id ? 600 : 400,
              background: activePage === n.id ? C.blueBg : 'transparent',
              color: activePage === n.id ? C.blue600 : C.textSec,
            }}>{n.label}</button>
          ))}
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{
          fontSize: 11, padding: '3px 9px', borderRadius: 4,
          background: C.amberBg, color: C.amber600, border: `1px solid ${C.amber100}`, fontWeight: 500,
        }}>⚠ 3 late submissions</span>
        <span style={{
          fontSize: 11, padding: '3px 8px', borderRadius: 4,
          background: C.blueBg, color: C.blue900, border: `1px solid ${C.blue100}`, fontWeight: 500,
        }}>Admin</span>
        <div style={{
          width: 30, height: 30, borderRadius: '50%', background: C.blue600,
          color: C.white, fontSize: 11, fontWeight: 600,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>AK</div>
      </div>
    </nav>
  );
}
