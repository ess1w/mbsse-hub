import React from 'react';
import { C } from '../tokens.js';

export default function TopNav({ activePage, setActivePage, user, onLogout }) {
  const isViewer = user?.role === 'viewer';

  const nav = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'directory', label: 'Partner Directory' },
    ...(!isViewer ? [{ id: 'form', label: 'Reporting Form' }] : []),
  ];

  const initials = user?.email
    ? user.email.slice(0, 2).toUpperCase()
    : '??';

  const roleLabel = user?.role
    ? user.role.charAt(0).toUpperCase() + user.role.slice(1)
    : '';

  const roleStyle = {
    admin:   { background: C.blueBg,   color: C.blue900,   border: `1px solid ${C.blue100}` },
    viewer:  { background: C.greenBg,  color: C.green900,  border: `1px solid ${C.green100}` },
    partner: { background: C.amberBg,  color: C.amber600,  border: `1px solid ${C.amber100}` },
  }[user?.role] ?? { background: C.borderLight, color: C.textSec, border: `1px solid ${C.border}` };

  return (
    <nav style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 20px', height: 48, background: C.white,
      borderBottom: `1px solid ${C.border}`, position: 'sticky', top: 0, zIndex: 100,
      boxShadow: '0 1px 3px rgba(0,0,0,.06)',
    }}>
      {/* Left — logo + nav */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          background: C.blue600, color: C.white, fontSize: 11, fontWeight: 600,
          padding: '4px 10px', borderRadius: 4,
        }}>MBSSE</div>
        <span style={{ fontSize: 13, fontWeight: 500 }}>SRGBV Coordination Hub</span>
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

      {/* Right — role badge + avatar + logout */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{
          fontSize: 11, padding: '3px 8px', borderRadius: 4, fontWeight: 500,
          ...roleStyle,
        }}>{roleLabel}</span>

        <div style={{
          width: 30, height: 30, borderRadius: '50%', background: C.blue600,
          color: C.white, fontSize: 11, fontWeight: 600,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          title: user?.email,
        }}>{initials}</div>

        {onLogout && (
          <button onClick={onLogout} style={{
            fontSize: 11, padding: '4px 10px', borderRadius: 4,
            border: `1px solid ${C.border}`, background: C.white,
            color: C.textSec, cursor: 'pointer',
          }}>Sign out</button>
        )}
      </div>
    </nav>
  );
}
