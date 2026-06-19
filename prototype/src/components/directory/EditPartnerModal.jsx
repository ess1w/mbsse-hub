import React, { useState } from 'react';
import { C } from '../../tokens.js';
import { organisationsApi } from '../../api/client.js';

const ORG_TYPES = ['CSO', 'UN Agency', 'Government', 'Other'];
const DISTRICTS = [
  'Bo', 'Bombali', 'Bonthe', 'Falaba', 'Kailahun', 'Kambia',
  'Karene', 'Kenema', 'Koinadugu', 'Kono', 'Moyamba', 'Port Loko',
  'Pujehun', 'Tonkolili', 'Western Area Rural', 'Western Area Urban',
];

const FIELD = {
  label: { fontSize: 11, fontWeight: 500, color: C.textSec, marginBottom: 4 },
  input: {
    width: '100%', padding: '7px 10px', fontSize: 12, borderRadius: 5,
    border: `1px solid ${C.border}`, color: C.text, background: C.white,
    boxSizing: 'border-box', outline: 'none',
  },
};

/** partner — UI-format partner object (camelCase keys from PartnerDirectory) */
export default function EditPartnerModal({ partner: p, onClose, onUpdated }) {
  const [form, setForm] = useState({
    org_name:     p.name         ?? '',
    org_type:     p.type         ?? 'CSO',
    focal_person: p.focalPerson  ?? '',
    email:        p.email === '—' ? '' : (p.email ?? ''),
    phone:        p.phone === '—' ? '' : (p.phone ?? ''),
    sla_signed:   p.sla_signed   ?? false,
    status:       p.status       ?? 'Pending',
    districts:    p.districts    ?? [],
    notes:        '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError]   = useState('');

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const toggleDistrict = (d) =>
    set('districts', form.districts.includes(d)
      ? form.districts.filter(x => x !== d)
      : [...form.districts, d]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.org_name.trim()) { setError('Organisation name is required.'); return; }
    setSaving(true);
    setError('');
    try {
      const updated = await organisationsApi.patch(p.id, {
        org_name:     form.org_name     || null,
        org_type:     form.org_type     || null,
        focal_person: form.focal_person || null,
        email:        form.email        || null,
        phone:        form.phone        || null,
        sla_signed:   form.sla_signed,
        status:       form.status       || null,
        districts:    form.districts,
        notes:        form.notes        || null,
      });
      onUpdated(updated);
    } catch (err) {
      setError(err.message || 'Failed to save changes.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,.45)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 300, padding: 20,
    }} onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={{
        background: C.white, borderRadius: 10, width: '100%', maxWidth: 580,
        maxHeight: '90vh', overflowY: 'auto',
        boxShadow: '0 8px 32px rgba(0,0,0,.18)',
      }}>
        {/* Header */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '16px 20px', borderBottom: `1px solid ${C.border}`,
        }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: C.text }}>Edit Organisation</div>
            <div style={{ fontSize: 11, color: C.textSec, marginTop: 2 }}>{p.name}</div>
          </div>
          <button onClick={onClose} style={{
            background: 'none', border: 'none', fontSize: 18, color: C.textMuted,
            cursor: 'pointer', padding: '0 4px', lineHeight: 1,
          }}>×</button>
        </div>

        <form onSubmit={handleSubmit} style={{ padding: '20px' }}>
          {error && (
            <div style={{
              background: C.redBg, border: `1px solid ${C.red}`, borderRadius: 6,
              padding: '9px 12px', fontSize: 12, color: C.red, marginBottom: 16,
            }}>{error}</div>
          )}

          {/* Name + Type */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 14, marginBottom: 14 }}>
            <div>
              <div style={FIELD.label}>Organisation name *</div>
              <input value={form.org_name} onChange={e => set('org_name', e.target.value)}
                style={FIELD.input} autoFocus />
            </div>
            <div>
              <div style={FIELD.label}>Type *</div>
              <select value={form.org_type} onChange={e => set('org_type', e.target.value)} style={FIELD.input}>
                {ORG_TYPES.map(t => <option key={t}>{t}</option>)}
              </select>
            </div>
          </div>

          {/* Focal person */}
          <div style={{ marginBottom: 14 }}>
            <div style={FIELD.label}>Focal person</div>
            <input value={form.focal_person} onChange={e => set('focal_person', e.target.value)}
              placeholder="Full name" style={FIELD.input} />
          </div>

          {/* Email + Phone */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 14 }}>
            <div>
              <div style={FIELD.label}>Email</div>
              <input type="email" value={form.email} onChange={e => set('email', e.target.value)}
                placeholder="focal@org.org" style={FIELD.input} />
            </div>
            <div>
              <div style={FIELD.label}>Phone</div>
              <input value={form.phone} onChange={e => set('phone', e.target.value)}
                placeholder="+232 76 000000" style={FIELD.input} />
            </div>
          </div>

          {/* Status + SLA */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 14 }}>
            <div>
              <div style={FIELD.label}>Status</div>
              <select value={form.status} onChange={e => set('status', e.target.value)} style={FIELD.input}>
                {['Pending', 'Active', 'Inactive'].map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, paddingTop: 20 }}>
              <input type="checkbox" id="sla_edit" checked={form.sla_signed}
                onChange={e => set('sla_signed', e.target.checked)}
                style={{ width: 15, height: 15, cursor: 'pointer' }} />
              <label htmlFor="sla_edit" style={{ fontSize: 12, color: C.text, cursor: 'pointer' }}>SLA signed</label>
            </div>
          </div>

          {/* Districts */}
          <div style={{ marginBottom: 14 }}>
            <div style={FIELD.label}>Districts covered</div>
            <div style={{
              display: 'flex', flexWrap: 'wrap', gap: 6,
              border: `1px solid ${C.border}`, borderRadius: 5,
              padding: '8px 10px', background: '#f9fbfc',
            }}>
              {DISTRICTS.map(d => {
                const selected = form.districts.includes(d);
                return (
                  <button key={d} type="button" onClick={() => toggleDistrict(d)} style={{
                    fontSize: 10, padding: '3px 8px', borderRadius: 4, cursor: 'pointer',
                    border: `1px solid ${selected ? C.blue600 : C.border}`,
                    background: selected ? C.blueBg : C.white,
                    color: selected ? C.blue600 : C.textSec,
                    fontWeight: selected ? 600 : 400,
                  }}>{d}</button>
                );
              })}
            </div>
            {form.districts.length > 0 && (
              <div style={{ fontSize: 10, color: C.textMuted, marginTop: 4 }}>
                {form.districts.length} district{form.districts.length !== 1 ? 's' : ''} selected
              </div>
            )}
          </div>

          {/* Notes */}
          <div style={{ marginBottom: 20 }}>
            <div style={FIELD.label}>Notes (internal)</div>
            <textarea value={form.notes} onChange={e => set('notes', e.target.value)}
              placeholder="Optional admin notes…" rows={2}
              style={{ ...FIELD.input, resize: 'vertical', fontFamily: 'inherit' }} />
          </div>

          {/* Footer */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button type="button" onClick={onClose} style={{
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
        </form>
      </div>
    </div>
  );
}
