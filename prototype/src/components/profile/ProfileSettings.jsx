import React, { useState, useEffect } from 'react';
import { C } from '../../tokens.js';
import { organisationsApi } from '../../api/client.js';

const FIELD = {
  label: { fontSize: 11, fontWeight: 500, color: C.textSec, marginBottom: 4 },
  input: {
    width: '100%', padding: '8px 11px', fontSize: 12, borderRadius: 5,
    border: `1px solid ${C.border}`, color: C.text, background: C.white,
    boxSizing: 'border-box', outline: 'none',
  },
  inputReadonly: {
    width: '100%', padding: '8px 11px', fontSize: 12, borderRadius: 5,
    border: `1px solid ${C.borderLight}`, color: C.textMuted,
    background: '#f8fafc', boxSizing: 'border-box',
  },
};

export default function ProfileSettings({ user }) {
  const [org, setOrg] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [form, setForm] = useState({ focal_person: '', email: '', phone: '' });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    if (!user?.org_id) { setLoading(false); return; }
    organisationsApi.get(user.org_id)
      .then(data => {
        setOrg(data);
        setForm({
          focal_person: data.focal_person || '',
          email:        data.email        || '',
          phone:        data.phone        || '',
        });
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [user?.org_id]);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSaveError('');
    setSaved(false);
    try {
      const updated = await organisationsApi.patch(user.org_id, {
        focal_person: form.focal_person || null,
        email:        form.email        || null,
        phone:        form.phone        || null,
      });
      setOrg(updated);
      setSaved(true);
      setEditing(false);
      setTimeout(() => setSaved(false), 4000);
    } catch (err) {
      setSaveError(err.message || 'Failed to save changes.');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setForm({
      focal_person: org?.focal_person || '',
      email:        org?.email        || '',
      phone:        org?.phone        || '',
    });
    setSaveError('');
    setEditing(false);
  };

  if (loading) return (
    <main style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: C.textMuted, fontSize: 13 }}>
      Loading profile…
    </main>
  );

  if (error) return (
    <main style={{ flex: 1, padding: '32px 28px', color: C.textSec, fontSize: 13 }}>
      <strong style={{ color: C.red }}>Could not load organisation profile:</strong> {error}
    </main>
  );

  if (!user?.org_id) return (
    <main style={{ flex: 1, padding: '32px 28px' }}>
      <div style={{ maxWidth: 480, background: C.amberBg, border: `1px solid ${C.amber100}`, borderRadius: 8, padding: '16px 20px', fontSize: 13, color: C.amber700 }}>
        Your account is not linked to a partner organisation. Contact an MBSSE administrator to assign your account.
      </div>
    </main>
  );

  return (
    <main style={{ flex: 1, padding: '24px 28px', maxWidth: 680 }}>
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 16, fontWeight: 600, color: C.text }}>Organisation Profile</div>
        <div style={{ fontSize: 12, color: C.textSec, marginTop: 3 }}>
          Update your focal person details and contact information.
        </div>
      </div>

      {/* Organisation info card (read-only) */}
      <div style={{
        background: C.white, border: `1px solid ${C.border}`, borderRadius: 8,
        padding: '16px 20px', marginBottom: 20,
      }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: C.textSec, marginBottom: 12, textTransform: 'uppercase', letterSpacing: '.06em', fontSize: 10 }}>
          Organisation
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
          <div>
            <div style={FIELD.label}>Organisation name</div>
            <div style={FIELD.inputReadonly}>{org?.org_name || '—'}</div>
          </div>
          <div>
            <div style={FIELD.label}>Type</div>
            <div style={FIELD.inputReadonly}>{org?.org_type || '—'}</div>
          </div>
          <div>
            <div style={FIELD.label}>Status</div>
            <div style={FIELD.inputReadonly}>{org?.status || '—'}</div>
          </div>
          <div>
            <div style={FIELD.label}>SLA signed</div>
            <div style={FIELD.inputReadonly}>{org?.sla_signed ? 'Yes' : 'Pending'}</div>
          </div>
        </div>
      </div>

      {/* Editable contact card */}
      <div style={{
        background: C.white, border: `1px solid ${C.border}`, borderRadius: 8,
        padding: '16px 20px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <div style={{ fontSize: 10, fontWeight: 600, color: C.textSec, textTransform: 'uppercase', letterSpacing: '.06em' }}>
            Focal Person &amp; Contact Details
          </div>
          {!editing && (
            <button onClick={() => setEditing(true)} style={{
              fontSize: 11, padding: '5px 12px', borderRadius: 5,
              border: `1px solid ${C.border}`, background: C.white,
              color: C.blue600, cursor: 'pointer', fontWeight: 500,
            }}>Edit</button>
          )}
        </div>

        {saved && (
          <div style={{
            background: C.greenBg, border: `1px solid ${C.green100}`, borderRadius: 6,
            padding: '9px 12px', fontSize: 12, color: C.green, marginBottom: 14,
          }}>Contact details updated successfully.</div>
        )}
        {saveError && (
          <div style={{
            background: C.redBg, border: `1px solid ${C.red}`, borderRadius: 6,
            padding: '9px 12px', fontSize: 12, color: C.red, marginBottom: 14,
          }}>{saveError}</div>
        )}

        <form onSubmit={handleSave}>
          <div style={{ display: 'grid', gap: 14 }}>
            <div>
              <div style={FIELD.label}>Focal person name</div>
              {editing
                ? <input value={form.focal_person} onChange={e => setForm(f => ({ ...f, focal_person: e.target.value }))}
                    placeholder="Full name" style={FIELD.input} autoFocus />
                : <div style={FIELD.inputReadonly}>{org?.focal_person || '—'}</div>
              }
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
              <div>
                <div style={FIELD.label}>Email address</div>
                {editing
                  ? <input type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                      placeholder="contact@organisation.org" style={FIELD.input} />
                  : <div style={FIELD.inputReadonly}>{org?.email || '—'}</div>
                }
              </div>
              <div>
                <div style={FIELD.label}>Phone number</div>
                {editing
                  ? <input value={form.phone} onChange={e => setForm(f => ({ ...f, phone: e.target.value }))}
                      placeholder="+232 76 000000" style={FIELD.input} />
                  : <div style={FIELD.inputReadonly}>{org?.phone || '—'}</div>
                }
              </div>
            </div>
          </div>

          {editing && (
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 20 }}>
              <button type="button" onClick={handleCancel} style={{
                padding: '8px 18px', fontSize: 12, borderRadius: 6,
                border: `1px solid ${C.border}`, background: C.white,
                color: C.textSec, cursor: 'pointer',
              }}>Cancel</button>
              <button type="submit" disabled={saving} style={{
                padding: '8px 20px', fontSize: 12, fontWeight: 500, borderRadius: 6,
                border: 'none', background: saving ? C.borderLight : C.blue600,
                color: saving ? C.textMuted : C.white, cursor: saving ? 'default' : 'pointer',
              }}>{saving ? 'Saving…' : 'Save changes'}</button>
            </div>
          )}
        </form>
      </div>
    </main>
  );
}
