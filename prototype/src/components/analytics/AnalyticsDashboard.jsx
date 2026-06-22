import React, { useEffect, useRef, useState } from 'react';
import { embedDashboard } from '@preset-sdk/embedded';
import { C } from '../../tokens.js';
import { apiFetch, usesDemoData } from '../../api/client.js';

/**
 * Embeds the Preset analytics dashboard using the Superset Embedded SDK.
 *
 * Required environment variables:
 *   VITE_PRESET_DOMAIN  – Preset workspace base URL, e.g.
 *                         https://83f65675.us2a.app.preset.io
 *
 * Required Render environment variables (backend / mbsse-hub-api):
 *   PRESET_API_TOKEN    – from manage.app.preset.io → user settings → API Keys
 *   PRESET_API_SECRET   – from the same page
 *
 * The backend endpoint GET /api/v1/analytics/guest-token exchanges those
 * credentials for a short-lived guest token (~5 min). The SDK refreshes it
 * automatically via the fetchGuestToken callback.
 */

const PRESET_DOMAIN = import.meta.env.VITE_PRESET_DOMAIN ?? '';
const DASHBOARD_ID  = import.meta.env.VITE_PRESET_DASHBOARD_ID ?? 'oBMOvaLJDme';

export default function AnalyticsDashboard() {
  const mountRef = useRef(null);
  const [status, setStatus] = useState('loading'); // loading | ready | error | unconfigured | demo

  useEffect(() => {
    if (!PRESET_DOMAIN) {
      setStatus('unconfigured');
      return;
    }

    if (usesDemoData()) {
      setStatus('demo');
      return;
    }

    let cancelled = false;

    async function mount() {
      try {
        await embedDashboard({
          id: DASHBOARD_ID,
          supersetDomain: PRESET_DOMAIN,
          mountPoint: mountRef.current,
          fetchGuestToken: async () => {
            const data = await apiFetch('/analytics/guest-token');
            return data.token;
          },
          dashboardUiConfig: {
            hideTitle: true,
            filters: { expanded: false },
          },
        });
        if (!cancelled) setStatus('ready');
      } catch (err) {
        console.error('Preset embed error:', err);
        if (!cancelled) setStatus('error');
      }
    }

    mount();
    return () => { cancelled = true; };
  }, []);

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', position: 'relative' }}>

      {status === 'loading' && (
        <div style={overlayStyle}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 12, color: C.textSec }}>Loading analytics…</div>
          </div>
        </div>
      )}

      {status === 'error' && (
        <Placeholder
          icon="⚠"
          title="Dashboard could not load"
          body="Check that PRESET_API_TOKEN and PRESET_API_SECRET are set on the API service in Render, then redeploy."
          accent={C.amber700}
          bg={C.amberBg}
        />
      )}

      {status === 'unconfigured' && (
        <Placeholder
          icon="📊"
          title="Analytics not configured"
          body={
            <>
              Set <code style={codeStyle}>VITE_PRESET_DOMAIN</code> on the frontend service in Render
              to your Preset workspace URL:{' '}
              <code style={codeStyle}>https://83f65675.us2a.app.preset.io</code>
            </>
          }
        />
      )}

      {status === 'demo' && (
        <Placeholder
          icon="📊"
          title="Analytics unavailable in demo mode"
          body="Connect to the live backend to view the Preset analytics dashboard."
        />
      )}

      {/* Force the SDK-generated iframe to fill its container */}
      <style>{`
        #preset-mount iframe {
          width: 100% !important;
          height: 100% !important;
          border: none !important;
          flex: 1;
        }
      `}</style>

      {/* SDK mount point — always in the DOM so the SDK can attach its iframe */}
      <div
        id="preset-mount"
        ref={mountRef}
        style={{
          flex: 1,
          display: status === 'ready' || status === 'loading' ? 'flex' : 'none',
          flexDirection: 'column',
          minHeight: 0,
        }}
      />
    </div>
  );
}

function Placeholder({ icon, title, body, accent = C.blue600, bg = C.blueBg }) {
  return (
    <div style={{
      flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: C.bg, padding: 40,
    }}>
      <div style={{
        maxWidth: 420, background: bg,
        border: `1px solid ${accent}22`,
        borderRadius: 12, padding: '32px 36px', textAlign: 'center',
      }}>
        <div style={{ fontSize: 32, marginBottom: 12 }}>{icon}</div>
        <div style={{ fontSize: 14, fontWeight: 600, color: C.text, marginBottom: 8 }}>{title}</div>
        <div style={{ fontSize: 12, color: C.textSec, lineHeight: 1.6 }}>{body}</div>
      </div>
    </div>
  );
}

const overlayStyle = {
  position: 'absolute', inset: 0,
  display: 'flex', alignItems: 'center', justifyContent: 'center',
  background: C.bg, zIndex: 1,
};

const codeStyle = {
  background: 'rgba(0,0,0,.06)', padding: '1px 5px',
  borderRadius: 3, fontFamily: 'monospace', fontSize: 11,
};
