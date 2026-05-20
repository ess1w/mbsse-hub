import React, { useState } from 'react';
import { C } from '../tokens.js';
import { authApi, auth } from '../api/client.js';

export default function Login({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await authApi.login(email, password);
      auth.setTokens({ access_token: data.access_token, refresh_token: data.refresh_token });
      auth.setUser({ email, role: data.role, org_id: data.org_id });
      onLogin({ email, role: data.role, org_id: data.org_id });
    } catch (err) {
      setError(err.message === 'HTTP 401' ? 'Incorrect email or password.' : err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: C.bg,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    }}>
      <div style={{ width: 380 }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            background: C.blue900,
            color: C.white,
            padding: '8px 18px',
            borderRadius: 8,
            marginBottom: 16,
          }}>
            <span style={{ fontSize: 18 }}>🎓</span>
            <span style={{ fontWeight: 700, fontSize: 14, letterSpacing: 0.5 }}>MBSSE</span>
          </div>
          <h1 style={{ fontSize: 20, fontWeight: 700, color: C.text, margin: '0 0 4px' }}>
            School Safety Coordination Hub
          </h1>
          <p style={{ fontSize: 13, color: C.textSec, margin: 0 }}>
            Sign in to your account
          </p>
        </div>

        {/* Card */}
        <div style={{
          background: C.white,
          border: `1px solid ${C.border}`,
          borderRadius: 12,
          padding: 32,
          boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
        }}>
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
                marginTop: 14,
                padding: '8px 12px',
                background: C.redBg,
                border: `1px solid ${C.red100}`,
                borderRadius: 6,
                color: C.red900,
                fontSize: 12,
              }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              style={{
                marginTop: 20,
                width: '100%',
                padding: '10px 0',
                background: loading ? C.blue200 : C.blue700,
                color: C.white,
                border: 'none',
                borderRadius: 7,
                fontSize: 13,
                fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'background 0.15s',
              }}
            >
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        </div>

        <p style={{ textAlign: 'center', marginTop: 20, fontSize: 11, color: C.textMuted }}>
          Ministry of Basic and Senior Secondary Education · Sierra Leone
        </p>
      </div>
    </div>
  );
}

const labelStyle = {
  display: 'block',
  fontSize: 12,
  fontWeight: 600,
  color: C.text,
  marginBottom: 6,
};

const inputStyle = {
  width: '100%',
  padding: '8px 10px',
  fontSize: 13,
  border: `1px solid ${C.border}`,
  borderRadius: 6,
  outline: 'none',
  boxSizing: 'border-box',
  color: C.text,
  background: C.white,
};
