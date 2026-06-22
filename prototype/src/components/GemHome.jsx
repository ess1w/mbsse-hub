import React from 'react';
import { C } from '../tokens.js';

const CARDS = [
  {
    icon: '📋',
    title: 'Submit a monthly report',
    description: 'Record your school-level GBV awareness activities for the current month.',
    buttonLabel: 'Submit report',
    page: 'gem',
  },
  {
    icon: '📊',
    title: 'View the analytics dashboard',
    description: 'Explore programme-wide data and trends across all partner and GEM activities.',
    buttonLabel: 'View analytics',
    page: 'analytics',
  },
];

export default function GemHome({ setActivePage, user }) {
  return (
    <main style={{
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px 24px',
      background: C.bg,
      minHeight: 0,
    }}>
      {/* Header */}
      <div style={{ textAlign: 'center', maxWidth: 520, marginBottom: 40 }}>
        <div style={{
          display: 'inline-block',
          background: C.blueBg,
          border: `1px solid ${C.blue100}`,
          borderRadius: 12,
          padding: '8px 16px',
          fontSize: 12,
          color: C.blue900,
          fontWeight: 500,
          marginBottom: 16,
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
          Use this hub to submit your monthly GEM coordinator reports and view programme analytics.
        </p>
      </div>

      {/* Action cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: 20,
        width: '100%',
        maxWidth: 560,
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

      {user?.full_name && (
        <div style={{ marginTop: 32, fontSize: 11, color: C.textMuted }}>
          Logged in as <strong style={{ color: C.textSec }}>{user.full_name}</strong> · GEM Coordinator
        </div>
      )}
    </main>
  );
}
