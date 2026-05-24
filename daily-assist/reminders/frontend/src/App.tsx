import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { Authenticator, useAuthenticator } from '@aws-amplify/ui-react';
import { RemindersList } from './components/RemindersList';
import { AppSelector } from './components/AppSelector';
import './App.css';

const APP_TITLES: Record<string, string> = {
  '/reminders': 'Daily Assist — Reminders',
};

function AppShell() {
  const { route, signOut, user, skipVerification } = useAuthenticator();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (route === 'verifyUser') skipVerification();
  }, [route, skipVerification]);

  if (route !== 'authenticated') {
    return (
      <div className="login-page">
        <div className="login-container">
          <h1 className="login-title">Poulomi & Subhayan</h1>
          <Authenticator hideSignUp />
        </div>
      </div>
    );
  }

  const title = APP_TITLES[location.pathname];

  return (
    <main className="app-container">
      <header className="app-header">
        <div className="header-left">
          {title && (
            <button className="back-btn" onClick={() => navigate('/')}>← Home</button>
          )}
          <h1>{title ?? 'Daily Assist'}</h1>
        </div>
        <div className="user-info">
          <span>Welcome, {user?.signInDetails?.loginId}</span>
          <button onClick={signOut} className="sign-out-btn">Sign Out</button>
        </div>
      </header>

      <Routes>
        <Route path="/" element={<AppSelector />} />
        <Route path="/reminders" element={<RemindersList />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </main>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Authenticator.Provider>
        <AppShell />
      </Authenticator.Provider>
    </BrowserRouter>
  );
}

export default App;
