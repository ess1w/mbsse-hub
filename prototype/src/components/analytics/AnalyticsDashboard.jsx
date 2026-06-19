import React, { useState } from 'react';
import { C } from '../../tokens.js';

/**
 * Embeds the Apache Superset dashboard configured in VITE_SUPERSET_URL.
 *
 * Required Superset setup (add to superset_config.py):
 *   FEATURE_FLAGS = {"EMBEDDED_SUPERSET": True}
 *   TALISMAN_ENABLED = False          # disables X-Frame-Options blocking
 *   # OR keep Talisman but whitelist your Hub origin:
 *   # TALISMAN_CONFIG = {"content_security_policy": {"frame-ancestors": ["'self'", "https://your-hub-domain"]}}
 *   WTF_CSRF_ENABLED = False          # only for dev/pilot — re-enable in production with proper CSRF setup
 *
 * Dashboard URL format (append ?standalone=true to hide Superset nav):
 *   https://your-superset-host/superset/dashboard/<slug-or-id>/?standalone=true
 *
 * Set in prototype/.env.local (development) or in Render environment variables (pilot):
 *   VITE_SUPERSET_URL=https://your-superset-host/superset/dashboard/<id>/?standalone=true
 */

const SUPERSET_URL = import.meta.env.VITE_SUPERSET_URL ?? '';

const isConfigured = SUPERSET_URL !== '' && !SUPERSET_URL.includes('your-superset-host');
const isLocalOnly  =
  SUPERSET_URL.includes('localhost') &&
  typeof window !== 'undefined' &&
  window.location.hostname !== 'localhost';

export default function AnalyticsDashboard() {
  const [iframeError, setIframeError] = useState(false);

  // Not configured at all
  if (!isConfigured) {
    return <Placeholder reason="not-configured" />;
  }

  // Configured but points at localhost while we're on a remote host
  if (isLocalOnly) {
    return <Placeholder reason="local-only" />;
  }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {iframeError && (
        <div style={{
          background: C.amberBg, borderBottom: `1px solid ${C.amber100}`,
          padding: '8px 16px', fontSize: 11, color: C.amber700, display: 'flex',
          alignItems: 'center', gap: 8,
        }}>
          <span>⚠</span>
          <span>
            The Superset dashboard could not load. Check that Superset is running,
            <code style={{ background: 'rgba(0,0,0,.06)', padding: '1px 5px', borderRadius: 3, margin: '0 3px' }}>TALISMAN_ENABLED = False</code>
            is set in <code style={{ background: 'rgba(0,0,0,.06)', padding: '1px 5px', borderRadius: 3 }}>superset_config.py</code>,
            and the URL ends with <code style={{ background: 'rgba(0,0,0,.06)', padding: '1px 5px', borderRadius: 3 }}>?standalone=true</code>.
          </span>
        </div>
      )}
      <iframe
        key={SUPERSET_URL}
        src={SUPERSET_URL}
        title="MBSSE Analytics Dashboard — Apache Superset"
        frameBorder="0"
        allowTransparency="true"
        onError={() => setIframeError(true)}
        style={{ flex: 1, width: '100%', height: '100%', border: 'none' }}
      />
    </div>
  );
}

function Placeholder({ reason }) {
  const isNotConfigured = reason === 'not-configured';
  return (
    <main style={{ flex: 1, padding: '40px 24px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{
        maxWidth: 580, width: '100%', textAlign: 'center',
        background: C.white, border: `1px solid ${C.border}`,
        borderRadius: 10, padding: '40px 36px',
        boxShadow: '0 1px 4px rgba(0,0,0,.05)',
      }}>
        {/* Superset icon */}
        <div style={{
          width: 52, height: 52, borderRadius: 12, margin: '0 auto 18px',
          background: C.blueBg, border: `1px solid ${C.blue100}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 24,
        }}>📊</div>

        <div style={{ fontSize: 15, fontWeight: 600, color: C.text, marginBottom: 8 }}>
          Analytics Dashboard
        </div>

        {isNotConfigured ? (
          <>
            <div style={{ fontSize: 12, color: C.textSec, lineHeight: 1.7, marginBottom: 20 }}>
              Set <code style={codeStyle}>VITE_SUPERSET_URL</code> to your Superset dashboard
              URL to embed it here. Add <code style={codeStyle}>?standalone=true</code> to the
              URL to hide the Superset navigation bar.
            </div>
            <div style={{
              textAlign: 'left', background: C.bg, border: `1px solid ${C.border}`,
              borderRadius: 6, padding: '12px 16px', fontSize: 11, fontFamily: 'monospace',
              color: C.text, lineHeight: 1.8,
            }}>
              <div style={{ color: C.textMuted, fontFamily: 'sans-serif', fontSize: 10, marginBottom: 6 }}>
                prototype/.env.local
              </div>
              VITE_SUPERSET_URL=https://your-superset-host/superset/dashboard/&lt;id&gt;/?standalone=true
            </div>
            <div style={{ marginTop: 16, fontSize: 11, color: C.textMuted, lineHeight: 1.6 }}>
              Also add this to <code style={codeStyle}>superset_config.py</code> to allow embedding:
              <div style={{
                textAlign: 'left', marginTop: 8, background: C.bg, border: `1px solid ${C.border}`,
                borderRadius: 6, padding: '10px 14px', fontFamily: 'monospace', fontSize: 11,
                color: C.text, lineHeight: 1.8,
              }}>
                {'FEATURE_FLAGS = {"EMBEDDED_SUPERSET": True}'}<br />
                {'TALISMAN_ENABLED = False'}
              </div>
            </div>
          </>
        ) : (
          <div style={{ fontSize: 12, color: C.textSec, lineHeight: 1.7 }}>
            The dashboard URL points to a local Superset instance. When deployed to Render,
            set <code style={codeStyle}>VITE_SUPERSET_URL</code> in the Render environment
            variables to a publicly accessible Superset URL.
          </div>
        )}
      </div>
    </main>
  );
}

const codeStyle = {
  background: C.bg, padding: '1px 5px', borderRadius: 3,
  fontFamily: 'monospace', fontSize: '0.95em',
};
