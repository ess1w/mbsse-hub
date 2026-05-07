import React, { useState } from 'react';
import TopNav from './components/TopNav.jsx';
import Sidebar from './components/Sidebar.jsx';
import Dashboard from './components/Dashboard.jsx';
import PartnerDirectory from './components/directory/PartnerDirectory.jsx';
import ReportingForm from './components/form/ReportingForm.jsx';
import { C } from './tokens.js';

export default function App() {
  const [activePage, setActivePage] = useState('dashboard');

  const showSidebar = activePage !== 'form';

  return (
    <div style={{ fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif", fontSize: 13, color: C.text, background: C.bg, minHeight: '100vh' }}>
      <TopNav activePage={activePage} setActivePage={setActivePage} />
      <div style={{ display: 'flex', minHeight: 'calc(100vh - 48px)' }}>
        {showSidebar && <Sidebar activePage={activePage} setActivePage={setActivePage} />}
        {activePage === 'dashboard' && <Dashboard setActivePage={setActivePage} />}
        {activePage === 'directory' && <PartnerDirectory />}
        {activePage === 'form' && <ReportingForm />}
      </div>
    </div>
  );
}
