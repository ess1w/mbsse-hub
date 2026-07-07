import React, { useState } from 'react';
import TopNav from './components/TopNav.jsx';
import Sidebar from './components/Sidebar.jsx';
import Dashboard from './components/Dashboard.jsx';
import PartnerDirectory from './components/directory/PartnerDirectory.jsx';
import ReportingForm from './components/form/ReportingForm.jsx';
import GemCoordinatorForm from './components/form/GemCoordinatorForm.jsx';
import UserManagement from './components/admin/UserManagement.jsx';
import ReportingPeriods from './components/admin/ReportingPeriods.jsx';
import ActivityReports from './components/reports/ActivityReports.jsx';
import ExportData from './components/reports/ExportData.jsx';
import Submissions from './components/submissions/Submissions.jsx';
import AnalyticsDashboard from './components/analytics/AnalyticsDashboard.jsx';
import ProfileSettings from './components/profile/ProfileSettings.jsx';
import PartnerHome from './components/PartnerHome.jsx';
import AdminHome from './components/AdminHome.jsx';
import GemHome from './components/GemHome.jsx';
import GemOfficerHome from './components/GemOfficerHome.jsx';
import GemReview from './components/gem/GemReview.jsx';
import ForcePasswordChange from './components/ForcePasswordChange.jsx';
import Login from './components/Login.jsx';
import { C } from './tokens.js';
import { auth, authApi } from './api/client.js';

export default function App() {
  const [activePage, setActivePage] = useState('dashboard');
  // Initialise from localStorage so a page refresh keeps the user logged in
  const [user, setUser] = useState(() => auth.getUser());

  const showSidebar = activePage !== 'form';

  function handleLogin(userData) {
    setUser(userData);
    const landingByRole = {
      partner: 'partner-home', gem_coordinator: 'gem-home',
      admin: 'admin-home', gem_district_officer: 'gem-officer-home',
    };
    setActivePage(landingByRole[userData.role] ?? 'dashboard');
  }

  // Forced password change after an admin reset
  function clearForcedChange() {
    const u = { ...user, must_change_password: false };
    auth.setUser(u);
    setUser(u);
  }

  async function handleLogout() {
    try { await authApi.logout(); } catch { /* ignore */ }
    auth.clear();
    setUser(null);
    setActivePage('dashboard');
  }

  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  if (user.must_change_password) {
    return <ForcePasswordChange user={user} onDone={clearForcedChange} onLogout={handleLogout} />;
  }

  return (
    <div style={{
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      fontSize: 13,
      color: C.text,
      background: C.bg,
      minHeight: '100vh',
    }}>
      <TopNav
        activePage={activePage}
        setActivePage={setActivePage}
        user={user}
        onLogout={handleLogout}
      />
      <div style={{ display: 'flex', minHeight: 'calc(100vh - 50px)' }}>
        {showSidebar && <Sidebar activePage={activePage} setActivePage={setActivePage} user={user} />}
        {activePage === 'dashboard'  && <Dashboard setActivePage={setActivePage} user={user} />}
        {activePage === 'directory'  && <PartnerDirectory user={user} />}
        {activePage === 'form'       && <ReportingForm user={user} setActivePage={setActivePage} />}
        {activePage === 'gem'        && <GemCoordinatorForm user={user} setActivePage={setActivePage} />}
        {activePage === 'users'      && <UserManagement user={user} />}
        {activePage === 'periods'    && <ReportingPeriods />}
        {activePage === 'reports'     && <ActivityReports user={user} />}
        {activePage === 'submissions' && <Submissions user={user} />}
        {activePage === 'export'      && <ExportData />}
        {activePage === 'analytics'   && <AnalyticsDashboard />}
        {activePage === 'profile'     && <ProfileSettings user={user} />}
        {activePage === 'partner-home' && <PartnerHome setActivePage={setActivePage} user={user} />}
        {activePage === 'admin-home'   && <AdminHome setActivePage={setActivePage} user={user} />}
        {activePage === 'gem-home'     && <GemHome setActivePage={setActivePage} user={user} />}
        {activePage === 'gem-officer-home' && <GemOfficerHome setActivePage={setActivePage} user={user} />}
        {activePage === 'gem-review'   && <GemReview user={user} />}
      </div>
    </div>
  );
}
