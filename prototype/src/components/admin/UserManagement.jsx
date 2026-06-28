import React, { useState, useMemo, useEffect } from 'react';
import { C } from '../../tokens.js';
import { usersApi, usesDemoData } from '../../api/client.js';

// ── Role definitions ────────────────────────────────────────────────────────

const ROLE_META = {
  admin: {
    label: 'Admin',
    desc: 'Full access — manage users, verify submissions, configure system settings',
    badge: { background: C.redBg, color: C.red900, border: `1px solid ${C.red100}` },
    avatar: { background: C.redBg, color: C.red700 },
  },
  partner: {
    label: 'Partner',
    desc: 'Can create and submit activity reports for their linked organisation only',
    badge: { background: C.blueBg, color: C.blue900, border: `1px solid ${C.blue100}` },
    avatar: { background: C.blueBg, color: C.blue700 },
  },
  viewer: {
    label: 'Viewer',
    desc: 'Read-only access to dashboard and reports — cannot submit or manage data',
    badge: { background: C.borderLight, color: C.textSec, border: `1px solid ${C.border}` },
    avatar: { background: C.borderLight, color: C.textSec },
  },
  gem_coordinator: {
    label: 'GEM Coordinator',
    desc: 'Can submit monthly GEM Coordinator reports — dashboard and analytics access only',
    badge: { background: C.greenBg, color: C.green900, border: `1px solid ${C.green100}` },
    avatar: { background: C.greenBg, color: C.green700 },
  },
};

const ORGS = [
  'ActionAid Sierra Leone', 'BRAC Sierra Leone', 'Caritas Makeni', 'Catholic Relief Services',
  'CAUSE Canada', 'ChildFund SL', 'Concern Worldwide SL', 'COOPI Sierra Leone',
  'Equal Access SL', 'FAWE Sierra Leone', 'GIZ Sierra Leone', 'Girl Child Network SL',
  'IRC Sierra Leone', 'Mercy Corps SL', 'NaCSA', 'Plan International',
  'Restless Development SL', 'Save the Children SL', 'Street Child of Sierra Leone',
  'UNICEF Sierra Leone', 'Welthungerhilfe SL', 'World Vision SL',
];

// ── Mock data ────────────────────────────────────────────────────────────────

let _nextId = 8;
const INIT_USERS = [
  { id: 1, name: 'Aminata Sesay',    email: 'admin@mbsse.gov.sl',              role: 'admin',   org: null,                          status: 'Active',   lastLogin: '2026-05-19', invitePending: false },
  { id: 2, name: 'Salaymatu Kamara', email: 's.kamara@plan-international.org', role: 'partner', org: 'Plan International',          status: 'Active',   lastLogin: '2026-05-15', invitePending: false },
  { id: 3, name: 'Ibrahim Koroma',   email: 'i.koroma@savethechildren.org',    role: 'partner', org: 'Save the Children SL',        status: 'Active',   lastLogin: '2026-05-10', invitePending: false },
  { id: 4, name: 'Fatmata Bangura',  email: 'f.bangura@unicef.org',           role: 'viewer',  org: null,                          status: 'Active',   lastLogin: '2026-04-28', invitePending: false },
  { id: 5, name: 'Mohamed Conteh',   email: 'm.conteh@streetchildsl.org',     role: 'partner', org: 'Street Child of Sierra Leone', status: 'Active',   lastLogin: null,         invitePending: true  },
  { id: 6, name: 'Hawa Jalloh',      email: 'h.jalloh@worldvision.org',       role: 'partner', org: 'World Vision SL',             status: 'Inactive', lastLogin: '2026-02-14', invitePending: false },
  { id: 7, name: 'David Mansaray',   email: 'd.mansaray@mbsse.gov.sl',        role: 'viewer',  org: null,                          status: 'Active',   lastLogin: '2026-05-18', invitePending: false },
];

// ── Helpers ──────────────────────────────────────────────────────────────────

const initials = (name) => name.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase();

const fmtDate = (iso) => iso
  ? new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
  : null;

// ── Sub-components ───────────────────────────────────────────────────────────

const RoleBadge = ({ role }) => {
  const meta = ROLE_META[role] ?? ROLE_META.viewer;
  return (
    <span style={{ ...meta.badge, fontSize: 10, padding: '2px 9px', borderRadius: 10, fontWeight: 500, display: 'inline-block', whiteSpace: 'nowrap' }}>
      {meta.label}
    </span>
  );
};

const StatusBadge = ({ status, pending }) => {
  if (pending) {
    return <span style={{ background: C.amberBg, color: C.amber600, border: `1px solid ${C.amber100}`, fontSize: 10, padding: '2px 9px', borderRadius: 10, fontWeight: 500, display: 'inline-block' }}>Invite pending</span>;
  }
  const s = status === 'Active'
    ? { background: C.greenBg, color: C.green900, border: `1px solid ${C.green100}` }
    : { background: C.borderLight, color: C.textMuted, border: `1px solid ${C.border}` };
  return <span style={{ ...s, fontSize: 10, padding: '2px 9px', borderRadius: 10, fontWeight: 500, display: 'inline-block' }}>{status}</span>;
};

// ── PanelInput must live outside UserManagement so React doesn't remount it
// on every keystroke (defining it inside the component creates a new function
// identity each render, which causes React to unmount/remount the input and
// lose focus after every character typed).
function PanelInput({ fieldKey, placeholder, type = 'text', value, error, onChange }) {
  return (
    <input
      value={value}
      onChange={e => onChange(fieldKey, e.target.value)}
      type={type}
      placeholder={placeholder}
      style={{
        width: '100%', height: 36,
        border: `1px solid ${error ? C.red500 : C.border}`,
        borderRadius: 6, padding: '0 10px', fontSize: 12,
        boxSizing: 'border-box', outline: 'none', color: C.text,
      }}
    />
  );
}

// ── Main component ───────────────────────────────────────────────────────────

const BLANK_FORM = { name: '', email: '', role: 'partner', org: '', sendInvite: true };

export default function UserManagement() {
  const [users, setUsers]               = useState(INIT_USERS);

  // Load real users from the backend (falls back to demo list in demo mode)
  useEffect(() => {
    if (usesDemoData()) return;
    usersApi.list()
      .then(rows => { if (Array.isArray(rows)) setUsers(rows); })
      .catch(() => {});
  }, []);
  const [search, setSearch]             = useState('');
  const [filterRole, setFilterRole]     = useState('');
  const [filterStatus, setFilterStatus] = useState('All statuses');
  const [expandedId, setExpandedId]     = useState(null);
  const [panelOpen, setPanelOpen]       = useState(false);
  const [editUser, setEditUser]         = useState(null);
  const [panelForm, setPanelForm]       = useState(BLANK_FORM);
  const [panelErrors, setPanelErrors]   = useState({});
  const [confirmId, setConfirmId]       = useState(null);   // id pending deactivation confirm
  const [toast, setToast]               = useState(null);   // { msg, type }

  // ── Stats ──────────────────────────────────────────────────────────────────

  const stats = useMemo(() => ({
    total:    users.length,
    admins:   users.filter(u => u.role === 'admin').length,
    partners: users.filter(u => u.role === 'partner').length,
    viewers:  users.filter(u => u.role === 'viewer').length,
    gemCoords: users.filter(u => u.role === 'gem_coordinator').length,
    inactive: users.filter(u => u.status === 'Inactive').length,
    pending:  users.filter(u => u.invitePending).length,
  }), [users]);

  // ── Filtered list ──────────────────────────────────────────────────────────

  const filtered = useMemo(() => {
    let list = users;
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(u =>
        u.name.toLowerCase().includes(q) ||
        u.email.toLowerCase().includes(q) ||
        (u.org ?? '').toLowerCase().includes(q)
      );
    }
    if (filterRole) list = list.filter(u => u.role === filterRole);
    if (filterStatus === 'Active')         list = list.filter(u => u.status === 'Active' && !u.invitePending);
    if (filterStatus === 'Inactive')       list = list.filter(u => u.status === 'Inactive');
    if (filterStatus === 'Invite pending') list = list.filter(u => u.invitePending);
    return list;
  }, [users, search, filterRole, filterStatus]);

  // ── Panel helpers ──────────────────────────────────────────────────────────

  const openAdd = () => {
    setEditUser(null);
    setPanelForm(BLANK_FORM);
    setPanelErrors({});
    setPanelOpen(true);
  };

  const openEdit = (u) => {
    setEditUser(u);
    setPanelForm({ name: u.name, email: u.email, role: u.role, org: u.org ?? '', sendInvite: false });
    setPanelErrors({});
    setPanelOpen(true);
  };

  const setPField = (key, val) => {
    setPanelForm(f => ({ ...f, [key]: val }));
    setPanelErrors(e => ({ ...e, [key]: null }));
  };

  const validate = () => {
    const errs = {};
    if (!panelForm.name.trim())  errs.name  = 'Full name is required';
    if (!panelForm.email.trim() || !panelForm.email.includes('@')) errs.email = 'A valid email address is required';
    if (panelForm.role === 'partner' && !panelForm.org) errs.org = 'Partner users must be linked to an organisation';
    if (!editUser && users.some(u => u.email.toLowerCase() === panelForm.email.trim().toLowerCase())) {
      errs.email = 'This email is already registered';
    }
    return errs;
  };

  const savePanel = () => {
    const errs = validate();
    if (Object.keys(errs).length) { setPanelErrors(errs); return; }

    if (editUser) {
      setUsers(prev => prev.map(u => u.id === editUser.id
        ? { ...u, name: panelForm.name.trim(), email: panelForm.email.trim(), role: panelForm.role, org: panelForm.role === 'partner' ? panelForm.org : null, invitePending: u.invitePending }
        : u
      ));
      showToast('User updated successfully', 'ok');
    } else {
      setUsers(prev => [...prev, {
        id: _nextId++,
        name:         panelForm.name.trim(),
        email:        panelForm.email.trim(),
        role:         panelForm.role,
        org:          panelForm.role === 'partner' ? panelForm.org : null,
        status:       'Active',
        lastLogin:    null,
        invitePending: panelForm.sendInvite,
      }]);
      showToast(panelForm.sendInvite ? 'User added — invitation email sent' : 'User added', 'ok');
    }
    setPanelOpen(false);
  };

  const toggleStatus = (id) => {
    setUsers(prev => prev.map(u => u.id === id
      ? { ...u, status: u.status === 'Active' ? 'Inactive' : 'Active', invitePending: false }
      : u
    ));
    const u = users.find(x => x.id === id);
    showToast(`${u?.name} ${u?.status === 'Active' ? 'deactivated' : 'reactivated'}`, 'ok');
    setConfirmId(null);
  };

  const removeUser = (id) => {
    const u = users.find(x => x.id === id);
    setUsers(prev => prev.filter(x => x.id !== id));
    setExpandedId(null);
    showToast(`${u?.name} removed`, 'warn');
  };

  const resendInvite = (id) => {
    setUsers(prev => prev.map(u => u.id === id ? { ...u, invitePending: true } : u));
    showToast('Invitation resent', 'ok');
  };

  const showToast = (msg, type) => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  // ── Style shortcuts ────────────────────────────────────────────────────────

  const selW = { fontSize: 11, padding: '5px 9px', border: `1px solid ${C.border}`, borderRadius: 5, background: C.white, color: C.text, cursor: 'pointer' };
  const thS  = { textAlign: 'left', padding: '9px 14px', fontSize: 10, fontWeight: 600, color: C.textSec, borderBottom: `1px solid ${C.border}`, background: '#f8fafc', whiteSpace: 'nowrap', userSelect: 'none' };
  const tdS  = { padding: '10px 14px', borderBottom: `1px solid ${C.borderLight}`, verticalAlign: 'middle' };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <main style={{ flex: 1, padding: '18px 20px', overflow: 'auto', minWidth: 0 }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 16 }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 3 }}>User Management</div>
          <div style={{ fontSize: 11, color: C.textSec }}>{stats.total} registered accounts · Admin section</div>
        </div>
        <button onClick={openAdd} style={{ padding: '8px 16px', background: C.blue600, color: C.white, border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 500, cursor: 'pointer' }}>
          + Add user
        </button>
      </div>

      {/* Stat strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 12, marginBottom: 16 }}>
        {[
          { label: 'Total accounts',    val: stats.total,     sub: 'All roles combined' },
          { label: 'Admins',            val: stats.admins,    sub: 'Full system access', accent: C.red500 },
          { label: 'Partners',          val: stats.partners,  sub: 'Report submitters' },
          { label: 'Viewers',           val: stats.viewers,   sub: 'Read-only access' },
          { label: 'GEM Coordinators',  val: stats.gemCoords, sub: 'Monthly reporters', accent: C.green700 },
          { label: 'Invite pending',    val: stats.pending,   sub: `${stats.inactive} inactive`, accent: stats.pending ? C.amber400 : undefined },
        ].map(({ label, val, sub, accent }) => (
          <div key={label} style={{ background: C.white, border: `1px solid ${C.border}`, borderLeft: accent ? `3px solid ${accent}` : `1px solid ${C.border}`, borderRadius: 8, padding: '12px 16px' }}>
            <div style={{ fontSize: 22, fontWeight: 600, color: accent ? (accent === C.red500 ? C.red700 : C.amber700) : C.text, lineHeight: 1 }}>{val}</div>
            <div style={{ fontSize: 11, color: C.textSec, marginTop: 4 }}>{label}</div>
            <div style={{ fontSize: 10, color: C.textMuted, marginTop: 2 }}>{sub}</div>
          </div>
        ))}
      </div>

      {/* Toolbar */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 14, background: C.white, padding: '10px 14px', borderRadius: 8, border: `1px solid ${C.border}`, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '5px 10px', border: `1px solid ${C.border}`, borderRadius: 5, background: '#f8fafc', flex: 1, maxWidth: 300 }}>
          <span style={{ fontSize: 12, color: C.textMuted }}>🔍</span>
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search name, email, organisation…"
            style={{ border: 'none', background: 'transparent', fontSize: 11, color: C.textSec, outline: 'none', width: '100%' }} />
        </div>
        <span style={{ fontSize: 11, fontWeight: 600, color: C.textSec }}>Filter:</span>
        <select value={filterRole} onChange={e => setFilterRole(e.target.value)} style={selW}>
          <option value="">All roles</option>
          <option value="admin">Admin</option>
          <option value="partner">Partner</option>
          <option value="viewer">Viewer</option>
          <option value="gem_coordinator">GEM Coordinator</option>
        </select>
        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} style={selW}>
          <option>All statuses</option>
          <option>Active</option>
          <option>Inactive</option>
          <option>Invite pending</option>
        </select>
        <button onClick={() => { setSearch(''); setFilterRole(''); setFilterStatus('All statuses'); }}
          style={{ fontSize: 11, padding: '5px 10px', borderRadius: 5, background: 'transparent', color: C.textSec, border: `1px solid ${C.border}`, cursor: 'pointer' }}>
          Reset
        </button>
        <span style={{ fontSize: 11, color: C.textMuted, marginLeft: 'auto' }}>Showing {filtered.length} of {stats.total} users</span>
      </div>

      {/* Table */}
      <div style={{ background: C.white, border: `1px solid ${C.border}`, borderRadius: 8, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
          <thead>
            <tr>
              <th style={thS}>User</th>
              <th style={thS}>Role</th>
              <th style={thS}>Organisation</th>
              <th style={thS}>Status</th>
              <th style={thS}>Last login</th>
              <th style={thS}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(u => {
              const isExpanded = expandedId === u.id;
              const meta = ROLE_META[u.role] ?? ROLE_META.viewer;
              return (
                <React.Fragment key={u.id}>
                  <tr
                    onClick={() => setExpandedId(isExpanded ? null : u.id)}
                    style={{ cursor: 'pointer', background: isExpanded ? C.blueBg : 'transparent' }}
                  >
                    {/* User */}
                    <td style={tdS}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div style={{ width: 34, height: 34, borderRadius: 8, ...meta.avatar, fontSize: 12, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                          {initials(u.name)}
                        </div>
                        <div>
                          <div style={{ fontWeight: 600, color: C.text, marginBottom: 1 }}>{u.name}</div>
                          <div style={{ fontSize: 10, color: C.textMuted }}>{u.email}</div>
                        </div>
                      </div>
                    </td>
                    <td style={tdS}><RoleBadge role={u.role} /></td>
                    <td style={{ ...tdS, color: u.org ? C.textSec : C.textMuted }}>{u.org ?? '—'}</td>
                    <td style={tdS}><StatusBadge status={u.status} pending={u.invitePending} /></td>
                    <td style={{ ...tdS, color: u.lastLogin ? C.textSec : C.textMuted }}>
                      {u.lastLogin ? fmtDate(u.lastLogin) : u.invitePending ? 'Never — invite sent' : 'Never'}
                    </td>
                    <td style={tdS} onClick={e => e.stopPropagation()}>
                      <div style={{ display: 'flex', gap: 12 }}>
                        <span onClick={() => openEdit(u)} style={{ fontSize: 11, color: C.blue600, cursor: 'pointer', fontWeight: 500 }}>Edit</span>
                        {u.invitePending && (
                          <span onClick={() => resendInvite(u.id)} style={{ fontSize: 11, color: C.amber700, cursor: 'pointer', fontWeight: 500 }}>Resend invite</span>
                        )}
                        {!u.invitePending && u.status === 'Active' && (
                          <span onClick={() => setConfirmId(u.id)} style={{ fontSize: 11, color: C.red700, cursor: 'pointer', fontWeight: 500 }}>Deactivate</span>
                        )}
                        {!u.invitePending && u.status === 'Inactive' && (
                          <span onClick={() => toggleStatus(u.id)} style={{ fontSize: 11, color: C.green700, cursor: 'pointer', fontWeight: 500 }}>Reactivate</span>
                        )}
                      </div>
                    </td>
                  </tr>

                  {/* Expanded row */}
                  {isExpanded && (
                    <tr>
                      <td colSpan={6} style={{ padding: 0 }}>
                        <div style={{ background: C.blueBg, borderTop: `1px solid ${C.blue100}`, padding: '14px 16px', display: 'flex', alignItems: 'flex-start', gap: 24 }}>
                          <div style={{ flex: 1 }}>
                            <div style={{ fontSize: 10, fontWeight: 700, color: C.textSec, textTransform: 'uppercase', letterSpacing: '.07em', marginBottom: 6 }}>
                              Access level — {meta.label}
                            </div>
                            <div style={{ fontSize: 11, color: C.textSec, lineHeight: 1.6, marginBottom: 8 }}>{meta.desc}</div>
                            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                              {u.role === 'admin' && ['Dashboard','Partner directory','All submissions','User management','Form settings','System settings'].map(p => (
                                <span key={p} style={{ fontSize: 10, padding: '2px 8px', background: C.redBg, color: C.red900, border: `1px solid ${C.red100}`, borderRadius: 4 }}>{p}</span>
                              ))}
                              {u.role === 'partner' && ['Dashboard (own data)','Reporting form','Own submissions'].map(p => (
                                <span key={p} style={{ fontSize: 10, padding: '2px 8px', background: C.blueBg, color: C.blue900, border: `1px solid ${C.blue100}`, borderRadius: 4 }}>{p}</span>
                              ))}
                              {u.role === 'viewer' && ['Dashboard (read-only)','Partner directory (read-only)','Activity reports (read-only)'].map(p => (
                                <span key={p} style={{ fontSize: 10, padding: '2px 8px', background: C.borderLight, color: C.textSec, border: `1px solid ${C.border}`, borderRadius: 4 }}>{p}</span>
                              ))}
                              {u.role === 'gem_coordinator' && ['Dashboard','Analytics','GEM Report (submit)'].map(p => (
                                <span key={p} style={{ fontSize: 10, padding: '2px 8px', background: C.greenBg, color: C.green900, border: `1px solid ${C.green100}`, borderRadius: 4 }}>{p}</span>
                              ))}
                            </div>
                          </div>
                          <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
                            <button onClick={() => openEdit(u)} style={{ padding: '6px 14px', background: C.blue600, color: C.white, border: 'none', borderRadius: 5, fontSize: 11, fontWeight: 500, cursor: 'pointer' }}>Edit user</button>
                            <button onClick={() => removeUser(u.id)} style={{ padding: '6px 14px', background: C.white, color: C.red700, border: `1px solid ${C.red100}`, borderRadius: 5, fontSize: 11, fontWeight: 500, cursor: 'pointer' }}>Remove user</button>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '36px 0', color: C.textMuted, fontSize: 12 }}>
                  No users match the current filters
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* ── Deactivate confirm modal ─────────────────────────────────────────── */}
      {confirmId && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.4)', zIndex: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: C.white, borderRadius: 10, padding: 24, width: 380, boxShadow: '0 8px 32px rgba(0,0,0,.2)' }}>
            <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 10 }}>Deactivate user?</div>
            <div style={{ fontSize: 12, color: C.textSec, lineHeight: 1.7, marginBottom: 20 }}>
              <strong>{users.find(u => u.id === confirmId)?.name}</strong> will no longer be able to log in.
              Their data is preserved and they can be reactivated at any time.
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button onClick={() => setConfirmId(null)} style={{ padding: '7px 16px', border: `1px solid ${C.border}`, borderRadius: 6, background: C.white, fontSize: 12, cursor: 'pointer', color: C.textSec }}>Cancel</button>
              <button onClick={() => toggleStatus(confirmId)} style={{ padding: '7px 16px', background: C.red500, color: C.white, border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 500, cursor: 'pointer' }}>Deactivate</button>
            </div>
          </div>
        </div>
      )}

      {/* ── Add / Edit panel ─────────────────────────────────────────────────── */}
      {panelOpen && (
        <>
          <div onClick={() => setPanelOpen(false)} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.3)', zIndex: 200 }} />
          <div style={{ position: 'fixed', top: 0, right: 0, bottom: 0, width: 460, background: C.white, zIndex: 201, boxShadow: '-4px 0 24px rgba(0,0,0,.15)', display: 'flex', flexDirection: 'column' }}>

            {/* Panel header */}
            <div style={{ padding: '18px 20px', borderBottom: `1px solid ${C.border}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
              <div style={{ fontSize: 14, fontWeight: 600 }}>{editUser ? 'Edit user' : 'Add new user'}</div>
              <span onClick={() => setPanelOpen(false)} style={{ fontSize: 18, color: C.textMuted, cursor: 'pointer', lineHeight: 1 }}>✕</span>
            </div>

            {/* Panel body */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: 18 }}>

              {/* Full name */}
              <div>
                <label style={{ fontSize: 11, fontWeight: 500, color: C.textSec, display: 'block', marginBottom: 5 }}>Full name *</label>
                <PanelInput fieldKey="name" placeholder="e.g. Aminata Sesay" value={panelForm.name} error={panelErrors.name} onChange={setPField} />
                {panelErrors.name && <div style={{ fontSize: 10, color: C.red700, marginTop: 3 }}>{panelErrors.name}</div>}
              </div>

              {/* Email */}
              <div>
                <label style={{ fontSize: 11, fontWeight: 500, color: C.textSec, display: 'block', marginBottom: 5 }}>Email address *</label>
                <PanelInput fieldKey="email" placeholder="user@organisation.org" type="email" value={panelForm.email} error={panelErrors.email} onChange={setPField} />
                {panelErrors.email && <div style={{ fontSize: 10, color: C.red700, marginTop: 3 }}>{panelErrors.email}</div>}
              </div>

              {/* Role */}
              <div>
                <label style={{ fontSize: 11, fontWeight: 500, color: C.textSec, display: 'block', marginBottom: 8 }}>Role *</label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {Object.entries(ROLE_META).map(([key, meta]) => {
                    const selected = panelForm.role === key;
                    return (
                      <div key={key} onClick={() => setPField('role', key)} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: '10px 12px', borderRadius: 7, cursor: 'pointer', border: `1.5px solid ${selected ? C.blue600 : C.border}`, background: selected ? C.blueBg : C.white, transition: 'all .1s' }}>
                        <div style={{ width: 16, height: 16, borderRadius: '50%', flexShrink: 0, marginTop: 2, border: `2px solid ${selected ? C.blue600 : C.border}`, background: selected ? C.blue600 : C.white, transition: 'all .1s' }} />
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                            <span style={{ fontSize: 12, fontWeight: 600, color: C.text }}>{meta.label}</span>
                            <span style={{ ...meta.badge, fontSize: 10, padding: '1px 7px', borderRadius: 10, fontWeight: 500 }}>{meta.label}</span>
                          </div>
                          <div style={{ fontSize: 11, color: C.textSec, lineHeight: 1.4 }}>{meta.desc}</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Organisation (partner only — not needed for other roles) */}
              {panelForm.role === 'partner' && (
                <div>
                  <label style={{ fontSize: 11, fontWeight: 500, color: C.textSec, display: 'block', marginBottom: 2 }}>Organisation *</label>
                  <div style={{ fontSize: 10, color: C.textMuted, marginBottom: 6 }}>Partner users can only submit reports for their linked organisation</div>
                  <select
                    value={panelForm.org}
                    onChange={e => setPField('org', e.target.value)}
                    style={{ width: '100%', height: 36, border: `1px solid ${panelErrors.org ? C.red500 : C.border}`, borderRadius: 6, padding: '0 10px', fontSize: 12, color: panelForm.org ? C.text : C.textMuted }}
                  >
                    <option value="">Select organisation…</option>
                    {ORGS.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                  {panelErrors.org && <div style={{ fontSize: 10, color: C.red700, marginTop: 3 }}>{panelErrors.org}</div>}
                </div>
              )}

              {/* Send invite toggle (new users only) */}
              {!editUser && (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 14px', background: '#f8fafc', borderRadius: 7, border: `1px solid ${C.borderLight}` }}>
                  <div>
                    <div style={{ fontSize: 11, fontWeight: 500, color: C.text }}>Send invitation email</div>
                    <div style={{ fontSize: 10, color: C.textMuted, marginTop: 2 }}>User receives a link to set their password</div>
                  </div>
                  <div
                    onClick={() => setPField('sendInvite', !panelForm.sendInvite)}
                    style={{ width: 40, height: 22, borderRadius: 11, cursor: 'pointer', flexShrink: 0, background: panelForm.sendInvite ? C.blue600 : C.border, position: 'relative', transition: 'background .2s' }}
                  >
                    <div style={{ width: 16, height: 16, borderRadius: '50%', background: C.white, position: 'absolute', top: 3, left: panelForm.sendInvite ? 21 : 3, transition: 'left .2s', boxShadow: '0 1px 3px rgba(0,0,0,.2)' }} />
                  </div>
                </div>
              )}
            </div>

            {/* Panel footer */}
            <div style={{ padding: '14px 20px', borderTop: `1px solid ${C.border}`, display: 'flex', gap: 8, justifyContent: 'flex-end', flexShrink: 0 }}>
              <button onClick={() => setPanelOpen(false)} style={{ padding: '8px 16px', border: `1px solid ${C.border}`, borderRadius: 6, background: C.white, fontSize: 12, cursor: 'pointer', color: C.textSec }}>Cancel</button>
              <button onClick={savePanel} style={{ padding: '8px 22px', background: C.blue600, color: C.white, border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 500, cursor: 'pointer' }}>
                {editUser ? 'Save changes' : panelForm.sendInvite ? 'Add user & send invite' : 'Add user'}
              </button>
            </div>
          </div>
        </>
      )}

      {/* ── Toast notification ───────────────────────────────────────────────── */}
      {toast && (
        <div style={{
          position: 'fixed', bottom: 24, left: '50%', transform: 'translateX(-50%)',
          background: toast.type === 'ok' ? C.green700 : C.amber700,
          color: C.white, padding: '10px 20px', borderRadius: 8, fontSize: 12, fontWeight: 500,
          boxShadow: '0 4px 16px rgba(0,0,0,.2)', zIndex: 400, pointerEvents: 'none',
        }}>
          {toast.msg}
        </div>
      )}

      <div style={{ position: 'fixed', bottom: 12, right: 14, fontSize: 10, color: C.textMuted, fontStyle: 'italic', pointerEvents: 'none' }}>
        Prototype v1.0 — MBSSE SRGBV Coordination Hub — May 2026
      </div>
    </main>
  );
}
