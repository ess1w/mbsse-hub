import React from 'react';
import { C } from '../tokens.js';
import coatOfArms from '../assets/Coat_of_arms_of_Sierra_Leone.png';
import bg from '../assets/app_backgrnd.jpg';

const CARDS = [
  {
    icon: '📋',
    title: 'Submit bi-monthly activity reports',
    description: 'Report on your organisation\'s SRGBV activities for the current reporting period.',
    buttonLabel: 'Submit report',
    page: 'form',
  },
  {
    icon: '🏢',
    title: 'Update your organisation\'s contact details',
    description: 'Keep your focal person, phone, email, and project information up to date.',
    buttonLabel: 'Update profile',
    page: 'profile',
  },
  {
    icon: '📊',
    title: 'View the analytics dashboard',
    description: 'Explore programme-wide data and trends across all partner activities.',
    buttonLabel: 'View analytics',
    page: 'analytics',
  },
];

export default function PartnerHome({ setActivePage, user }) {
  return (
    <main style={{
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px 24px',
      minHeight: 0,
      backgroundImage: `linear-gradient(rgba(247,249,251,.92), rgba(247,249,251,.92)), url(${bg})`,
      backgroundSize: 'cover', backgroundPosition: 'center', backgroundAttachment: 'fixed',
    }}>
      {/* Header */}
      <div style={{ textAlign: 'center', maxWidth: 560, marginBottom: 40 }}>
        <img src={coatOfArms} alt="Coat of Arms of Sierra Leone" style={{ height: 56, marginBottom: 10 }} />
        <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>Ministry of Basic and Senior Secondary Education</div>
        <div style={{
          display: 'inline-block',
          background: C.blueBg,
          border: `1px solid ${C.blue100}`,
          borderRadius: 12,
          padding: '6px 14px',
          fontSize: 11,
          color: C.blue900,
          fontWeight: 500,
          margin: '10px 0 16px',
        }}>
          SRGBV Coordination Hub
        </div>
        <h1 style={{
          fontSize: 26,
          fontWeight: 700,
          color: C.text,
          margin: '0 0 12px',
          lineHeight: 1.25,
        }}>
          Welcome{user?.full_name ? `, ${user.full_name.split(' ')[0]}` : ''}
        </h1>
        <p style={{
          fontSize: 14,
          color: C.textSec,
          lineHeight: 1.65,
          margin: 0,
        }}>
          Use this hub to manage your organisation's reporting, update your contact details, and track programme progress.
        </p>
      </div>

      {/* Action cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: 20,
        width: '100%',
        maxWidth: 820,
      }}>
        {CARDS.map(card => (
          <div key={card.page} style={{
            background: C.white,
            border: `1px solid ${C.border}`,
            borderRadius: 12,
            padding: '28px 24px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            gap: 12,
          }}>
            <div style={{
              width: 52,
              height: 52,
              borderRadius: 14,
              background: C.blueBg,
              border: `1px solid ${C.blue100}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 24,
            }}>
              {card.icon}
            </div>
            <div style={{ fontSize: 13, fontWeight: 600, color: C.text, lineHeight: 1.35 }}>
              {card.title}
            </div>
            <div style={{ fontSize: 12, color: C.textSec, lineHeight: 1.6, flex: 1 }}>
              {card.description}
            </div>
            <button
              onClick={() => setActivePage(card.page)}
              style={{
                marginTop: 4,
                padding: '9px 20px',
                background: C.blue600,
                color: C.white,
                border: 'none',
                borderRadius: 7,
                fontSize: 12,
                fontWeight: 500,
                cursor: 'pointer',
                width: '100%',
              }}
              onMouseEnter={e => e.currentTarget.style.background = C.blue700}
              onMouseLeave={e => e.currentTarget.style.background = C.blue600}
            >
              {card.buttonLabel}
            </button>
          </div>
        ))}
      </div>

      {user?.org_name && (
        <div style={{ marginTop: 32, fontSize: 11, color: C.textMuted }}>
          Logged in as <strong style={{ color: C.textSec }}>{user.org_name}</strong>
        </div>
      )}
    </main>
  );
}
