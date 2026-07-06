import React, { useState } from 'react';
import { C } from '../tokens.js';
import { authApi } from '../api/client.js';
import coatOfArms from '../assets/Coat_of_arms_of_Sierra_Leone.png';
import bg from '../assets/app_backgrnd.jpg';

export default function ForcePasswordChange({ user, onDone, onLogout }) {
  const [pw, setPw] = useState({ current: '', next: '', confirm: '' });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    if (pw.next.length < 8) { setError('New password must be at least 8 characters.'); return; }
    if (pw.next !== pw.confirm) { setError('New passwords do not match.'); return; }
    setSaving(true);
    try {
      await authApi.changePassword(pw.current, pw.next);
      onDone();
    } catch (err) {
      setError(err.message || 'Could not change password.');
    } finally {
      setSaving(false);
    }
  };

  const input = { width: '100%', padding: '9px 11px', fontSize: 13, borderRadius: 6, border: `1px solid ${C.border}`, boxSizing: 'border-box', outline: 'none' };
  const label = { fontSize: 12, fontWeight: 500, color: C.textSec, marginBottom: 5 };

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20,
      backgroundImage: `linear-gradient(rgba(247,249,251,.75), rgba(247,249,251,.75)), url(${bg})`,
      backgroundSize: 'cover', backgroundPosition: 'center',
    }}>
      <div style={{ background: C.white, border: `1px solid ${C.border}`, borderRadius: 12, padding: '28px 26px', width: '100%', maxWidth: 400, boxShadow: '0 8px 32px rgba(0,0,0,.10)' }}>
        <div style={{ textAlign: 'center', marginBottom: 18 }}>
          <img src={coatOfArms} alt="" style={{ height: 44, marginBottom: 10 }} />
          <div style={{ fontSize: 16, fontWeight: 700, color: C.text }}>Set a new password</div>
          <div style={{ fontSize: 12, color: C.textSec, marginTop: 6, lineHeight: 1.5 }}>
            Your password was reset by an administrator. Please choose a new password to continue{user?.full_name ? `, ${user.full_name.split(' ')[0]}` : ''}.
          </div>
        </div>
        {error && (
          <div style={{ background: C.redBg, border: `1px solid ${C.red}`, borderRadius: 6, padding: '9px 12px', fontSize: 12, color: C.red, marginBottom: 14 }}>{error}</div>
        )}
        <form onSubmit={submit}>
          <div style={{ display: 'grid', gap: 12 }}>
            <div>
              <div style={label}>Current (temporary) password</div>
              <input type="password" value={pw.current} onChange={e => setPw(p => ({ ...p, current: e.target.value }))} style={input} autoComplete="current-password" autoFocus />
            </div>
            <div>
              <div style={label}>New password</div>
              <input type="password" value={pw.next} onChange={e => setPw(p => ({ ...p, next: e.target.value }))} style={input} autoComplete="new-password" />
            </div>
            <div>
              <div style={label}>Confirm new password</div>
              <input type="password" value={pw.confirm} onChange={e => setPw(p => ({ ...p, confirm: e.target.value }))} style={input} autoComplete="new-password" />
            </div>
          </div>
          <button type="submit" disabled={saving} style={{
            marginTop: 18, width: '100%', padding: '10px', fontSize: 13, fontWeight: 600, borderRadius: 7,
            border: 'none', background: saving ? C.borderLight : C.blue600, color: saving ? C.textMuted : C.white, cursor: saving ? 'default' : 'pointer',
          }}>{saving ? 'Saving…' : 'Update password & continue'}</button>
        </form>
        {onLogout && (
          <div style={{ textAlign: 'center', marginTop: 14 }}>
            <button onClick={onLogout} style={{ background: 'none', border: 'none', color: C.textSec, fontSize: 11, cursor: 'pointer', textDecoration: 'underline' }}>Sign out instead</button>
          </div>
        )}
      </div>
    </div>
  );
}
