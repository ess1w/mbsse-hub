import React, { useState, useEffect, useRef } from 'react';
import { C } from '../../tokens.js';
import { organisationsApi, slaApi } from '../../api/client.js';

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

  // SLA documents
  const [slaDocs, setSlaDocs] = useState([]);
  const [slaUploading, setSlaUploading] = useState(false);
  const [slaError, setSlaError] = useState('');
  const slaInputRef = useRef(null);

  useEffect(() => {
    if (!user?.organisation_id) { setLoading(false); return; }
    organisationsApi.get(user.organisation_id)
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
  }, [user?.organisation_id]);

  const loadSla = () => {
    if (!user?.organisation_id) return;
    slaApi.list(user.organisation_id)
      .then(docs => setSlaDocs(Array.isArray(docs) ? docs : []))
      .catch(() => {});
  };
  useEffect(loadSla, [user?.organisation_id]);

  const handleSlaUpload = async (file) => {
    if (!file) return;
    setSlaError('');
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'doc', 'docx'].includes(ext)) {
      setSlaError('Only PDF or Word documents are allowed.');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setSlaError('File exceeds the 10 MB limit.');
      return;
    }
    setSlaUploading(true);
    try {
      await slaApi.upload(user.organisation_id, file);
      loadSla();
    } catch (err) {
      setSlaError(err.message || 'Upload failed.');
    } finally {
      setSlaUploading(false);
      if (slaInputRef.current) slaInputRef.current.value = '';
    }
  };

  const slaBadge = (status) => {
    const map = {
      approved: { bg: C.greenBg, color: C.green, label: 'Approved' },
      rejected: { bg: C.redBg, color: C.red, label: 'Rejected' },
      pending:  { bg: C.amberBg, color: C.amber700, label: 'Pending review' },
    };
    const s = map[status] || map.pending;
    return <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 10, background: s.bg, color: s.color, fontWeight: 600 }}>{s.label}</span>;
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSaveError('');
    setSaved(false);
    try {
      const updated = await organisationsApi.patch(user.organisation_id, {
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

  if (!user?.organisation_id) return (
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
        <div style={{ fontWeight: 600, color: C.textSec, marginBottom: 12, textTransform: 'uppercase', letterSpacing: '.06em', fontSize: 10 }}>
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

      {/* SLA document card */}
      <div style={{
        background: C.white, border: `1px solid ${C.border}`, borderRadius: 8,
        padding: '16px 20px', marginBottom: 20,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <div style={{ fontSize: 10, fontWeight: 600, color: C.textSec, textTransform: 'uppercase', letterSpacing: '.06em' }}>
            Service Level Agreement (SLA)
          </div>
          <input ref={slaInputRef} type="file" accept=".pdf,.doc,.docx" style={{ display: 'none' }}
            onChange={e => handleSlaUpload(e.target.files?.[0])} />
          <button onClick={() => slaInputRef.current?.click()} disabled={slaUploading} style={{
            fontSize: 11, padding: '5px 12px', borderRadius: 5,
            border: `1px solid ${C.blue600}`, background: slaUploading ? C.borderLight : C.blueBg,
            color: C.blue600, cursor: slaUploading ? 'default' : 'pointer', fontWeight: 500,
          }}>{slaUploading ? 'Uploading…' : '⬆ Upload SLA'}</button>
        </div>
        <div style={{ fontSize: 11, color: C.textSec, marginBottom: 12 }}>
          Upload your signed SLA as a PDF or Word document (max 10 MB). An MBSSE administrator will review and approve it.
        </div>
        {slaError && (
          <div style={{ background: C.redBg, border: `1px solid ${C.red}`, borderRadius: 6, padding: '9px 12px', fontSize: 12, color: C.red, marginBottom: 12 }}>{slaError}</div>
        )}
        {slaDocs.length === 0
          ? <div style={{ fontSize: 12, color: C.textMuted, fontStyle: 'italic' }}>No SLA document uploaded yet.</div>
          : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {slaDocs.map(d => (
                <div key={d.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px', border: `1px solid ${C.border}`, borderRadius: 6 }}>
                  <span style={{ fontSize: 18 }}>📄</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 500, color: C.text, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {d.storage_url ? <a href={d.storage_url} target="_blank" rel="noreferrer" style={{ color: C.blue600, textDecoration: 'none' }}>{d.original_filename}</a> : d.original_filename}
                    </div>
                    <div style={{ fontSize: 10, color: C.textMuted }}>{new Date(d.created_at).toLocaleDateString()}{d.review_notes ? ` · ${d.review_notes}` : ''}</div>
                  </div>
                  {slaBadge(d.status)}
                </div>
              ))}
            </div>
          )
        }
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
