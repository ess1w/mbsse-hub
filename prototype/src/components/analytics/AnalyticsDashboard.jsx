import React from 'react';
import { C } from '../../tokens.js';

// Configurable via VITE_METABASE_URL. Defaults to the local Metabase instance
// used in development. On a deployed site without a public Metabase, we show a
// placeholder instead of a broken localhost iframe.
const METABASE_URL =
  import.meta.env.VITE_METABASE_URL ||
  'http://localhost:3000/public/dashboard/2326d814-8f87-460f-b9f4-29879bb27a1c';

const isLocalOnly =
  METABASE_URL.includes('localhost') &&
  typeof window !== 'undefined' &&
  window.location.hostname !== 'localhost';

export default function AnalyticsDashboard() {
  if (isLocalOnly) {
    return (
      <main style={{ flex: 1, padding: '40px 24px' }}>
        <div style={{
          maxWidth: 560, margin: '0 auto', textAlign: 'center',
          background: C.white, border: `1px solid ${C.border}`,
          borderRadius: 8, padding: '40px 32px',
        }}>
          <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 8 }}>Analytics dashboard</div>
          <div style={{ fontSize: 12, color: C.textSec, lineHeight: 1.6 }}>
            The interactive analytics dashboard is served from a Metabase instance that
            isn&rsquo;t publicly deployed yet. Set <code style={{ background: C.bg, padding: '1px 5px', borderRadius: 3 }}>VITE_METABASE_URL</code> to
            a public Metabase dashboard URL to embed it here.
          </div>
        </div>
      </main>
    );
  }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <iframe
        src={METABASE_URL}
        title="MBSSE Analytics Dashboard"
        frameBorder="0"
        allowTransparency="true"
        style={{ flex: 1, width: '100%', height: '100%', border: 'none' }}
      />
    </div>
  );
}
