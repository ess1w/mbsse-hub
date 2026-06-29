import React from 'react';
import { C } from '../tokens.js';
import coatOfArms from '../assets/Coat_of_arms_of_Sierra_Leone.png';

export default function TopNav({ activePage, setActivePage, user, onLogout }) {
  const isViewer  = user?.role === 'viewer';
  const isPartner = user?.role === 'partner';

  // Role-aware home page — the title acts as the Home link
  const homePage = { admin: 'admin-home', partner: 'partner-home', gem_coordinator: 'gem-home' }[user?.role] ?? 'dashboard';
  const goHome = () => setActivePage(homePage);

  const nav = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'directory', label: 'Partner Directory' },
    ...(!isViewer ? [{ id: 'form', label: 'Reporting Form' }] : []),
  ];

  const initials = user?.email
    ? user.email.slice(0, 2).toUpperCase()
    : '??';

  const roleLabel = user?.role === 'gem_coordinator'
    ? 'GEM Coord.'
    : user?.role
      ? user.role.charAt(0).toUpperCase() + user.role.slice(1)
      : '';

  const roleStyle = {
    admin:           { background: C.blueBg,   color: C.blue900,   border: `1px solid ${C.blue100}` },
    viewer:          { background: C.greenBg,  color: C.green900,  border: `1px solid ${C.green100}` },
    partner:         { background: C.amberBg,  color: C.amber600,  border: `1px solid ${C.amber100}` },
    gem_coordinator: { background: C.greenBg,  color: C.green900,  border: `1px solid ${C.green100}` },
  }[user?.role] ?? { background: C.borderLight, color: C.textSec, border: `1px solid ${C.border}` };

  return (
    <>
      {/* Sierra Leone flag strip */}
      <div style={{ display: 'flex', height: 4 }}>
        <div style={{ flex: 1, background: C.blue600 }} />
        <div style={{ flex: 1, background: C.white, borderTop: `1px solid ${C.border}`, borderBottom: `1px solid ${C.border}` }} />
        <div style={{ flex: 1, background: C.slBlue }} />
      </div>

      <nav style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 20px', height: 46, background: C.white,
        borderBottom: `1px solid ${C.border}`,
        position: 'sticky', top: 4, zIndex: 100,
        boxShadow: '0 1px 3px rgba(0,0,0,.06)',
      }}>
        {/* Left — coat of arms + logo (links Home) + nav */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <img
            src={coatOfArms}
            alt="Coat of Arms of Sierra Leone"
            onClick={goHome}
            style={{ height: 30, width: 'auto', flexShrink: 0, cursor: 'pointer' }}
          />
          <div style={{
            background: C.blue600, color: C.white, fontSize: 11, fontWeight: 700,
            padding: '3px 10px', borderRadius: 4, letterSpacing: '0.04em',
          }}>MBSSE</div>
          <span
            onClick={goHome}
            title="Go to home"
            style={{ fontSize: 13, fontWeight: 500, color: C.text, cursor: 'pointer' }}
            onMouseEnter={e => e.currentTarget.style.color = C.blue600}
            onMouseLeave={e => e.currentTarget.style.color = C.text}
          >
            SRGBV Coordination Hub
          </span>

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

        {/* Right — role badge + profile link + avatar + logout */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{
            fontSize: 11, padding: '3px 8px', borderRadius: 4, fontWeight: 500,
            ...roleStyle,
          }}>{roleLabel}</span>

          <button onClick={() => setActivePage('profile')} style={{
            fontSize: 11, padding: '4px 10px', borderRadius: 4,
            border: `1px solid ${C.border}`,
            background: activePage === 'profile' ? C.blueBg : C.white,
            color: activePage === 'profile' ? C.blue600 : C.textSec,
            cursor: 'pointer',
          }}>{isPartner ? 'My Profile' : 'My Account'}</button>

          <div style={{
            width: 30, height: 30, borderRadius: '50%',
            background: C.blue600, color: C.white,
            fontSize: 11, fontWeight: 600,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
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
    </>
  );
}
