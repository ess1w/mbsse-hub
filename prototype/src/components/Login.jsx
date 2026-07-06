import React, { useState } from 'react';
import { C } from '../tokens.js';
import { authApi, auth, DEMO_MODE } from '../api/client.js';
import coatOfArms from '../assets/Coat_of_arms_of_Sierra_Leone.png';
import bg from '../assets/app_backgrnd.jpg';

export default function Login({ onLogin }) {
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]       = useState('');
  const [loading, setLoading]   = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await authApi.login(email, password);
      auth.setTokens({ access_token: data.access_token, refresh_token: data.refresh_token });
      const userData = {
        email, role: data.role, organisation_id: data.organisation_id,
        org_name: data.org_name, full_name: data.full_name,
        district_name: data.district_name,
        must_change_password: data.must_change_password,
      };
      auth.setUser(userData);
      onLogin(userData);
    } catch (err) {
      setError(
        err.message === 'HTTP 401' || err.message.includes('Incorrect')
          ? 'Incorrect email or password.'
          : err.message
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundImage: `linear-gradient(rgba(244,247,244,.72), rgba(244,247,244,.72)), url(${bg})`,
      backgroundSize: 'cover', backgroundPosition: 'center',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    }}>
      {/* Sierra Leone flag colour strip */}
      <div style={{ position: 'fixed', top: 0, left: 0, right: 0, display: 'flex', height: 5, zIndex: 10 }}>
        <div style={{ flex: 1, background: C.blue600 }} />
        <div style={{ flex: 1, background: C.white, borderTop: `1px solid ${C.border}`, borderBottom: `1px solid ${C.border}` }} />
        <div style={{ flex: 1, background: C.slBlue }} />
      </div>

      <div style={{ width: 400, paddingTop: 20 }}>
        {/* Government header */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <img
            src={coatOfArms}
            alt="Coat of Arms of Sierra Leone"
            style={{ height: 96, marginBottom: 14, filter: 'drop-shadow(0 2px 6px rgba(0,0,0,0.15))' }}
          />
          <div style={{
            fontSize: 10, fontWeight: 700, letterSpacing: '0.12em',
            textTransform: 'uppercase', color: C.blue600, marginBottom: 5,
          }}>
            Republic of Sierra Leone
          </div>
          <div style={{ fontSize: 13, fontWeight: 600, color: C.text, lineHeight: 1.4 }}>
            Ministry of Basic and Senior Secondary Education
          </div>
          <div style={{
            display: 'inline-block', marginTop: 10,
            background: C.blue600, color: C.white,
            fontSize: 11, fontWeight: 600, padding: '4px 14px',
            borderRadius: 4, letterSpacing: '0.04em',
          }}>
            SRGBV School Safety Coordination Hub
          </div>
        </div>

        {/* Demo credentials notice */}
        {DEMO_MODE && (
          <div style={{
            background: '#fffbeb', border: '1px solid #fcd34d', borderRadius: 8,
            padding: '10px 14px', marginBottom: 16, fontSize: 11, color: '#92400e', lineHeight: 1.6,
          }}>
            <strong>Demo mode</strong> — no backend connected. Use any of these to sign in:
            <div style={{ marginTop: 6, display: 'flex', flexDirection: 'column', gap: 2, fontFamily: 'monospace', fontSize: 11 }}>
              <span>admin@mbsse.gov.sl · demo2026 <span style={{ fontFamily: 'sans-serif', opacity: 0.7 }}>(Admin)</span></span>
              <span>partner@example.com · demo2026 <span style={{ fontFamily: 'sans-serif', opacity: 0.7 }}>(Partner)</span></span>
              <span>viewer@example.com · demo2026 <span style={{ fontFamily: 'sans-serif', opacity: 0.7 }}>(Viewer)</span></span>
            </div>
          </div>
        )}

        {/* Login card */}
        <div style={{
          background: C.white,
          border: `1px solid ${C.border}`,
          borderRadius: 12,
          padding: 32,
          boxShadow: '0 2px 12px rgba(0,0,0,0.07)',
        }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: C.text, marginBottom: 20 }}>
            Sign in to your account
          </div>

          <form onSubmit={handleSubmit}>
            <label style={labelStyle}>Email address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
              placeholder="you@example.com"
              style={inputStyle}
            />

            <label style={{ ...labelStyle, marginTop: 16 }}>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="••••••••"
              style={inputStyle}
            />

            {error && (
              <div style={{
                marginTop: 14, padding: '8px 12px',
                background: C.redBg, border: `1px solid ${C.red100}`,
                borderRadius: 6, color: C.red900, fontSize: 12,
              }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              style={{
                marginTop: 20, width: '100%', padding: '10px 0',
                background: loading ? C.blue200 : C.blue600,
                color: C.white, border: 'none', borderRadius: 7,
                fontSize: 13, fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'background 0.15s',
              }}
            >
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        </div>

        <p style={{ textAlign: 'center', marginTop: 20, fontSize: 11, color: C.textMuted }}>
          Supported by UNICEF Sierra Leone
        </p>
      </div>
    </div>
  );
}

const labelStyle = {
  display: 'block', fontSize: 12, fontWeight: 600,
  color: C.text, marginBottom: 6,
};

const inputStyle = {
  width: '100%', padding: '8px 10px', fontSize: 13,
  border: `1px solid ${C.border}`, borderRadius: 6,
  outline: 'none', boxSizing: 'border-box',
  color: C.text, background: C.white,
};
