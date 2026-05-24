import { useEffect } from 'react';
import { Authenticator, useAuthenticator } from '@aws-amplify/ui-react';
import { LanguageLearningApp } from './components/LanguageLearningApp';
import { authEnabled } from './utils/auth';
import './App.css';

function AppContent() {
  const { route, signOut, user, skipVerification } = useAuthenticator((context) => [
    context.route,
    context.user,
  ]);

  useEffect(() => {
    if (route === 'verifyUser') skipVerification();
  }, [route, skipVerification]);

  if (authEnabled && route !== 'authenticated') {
    return (
      <div className="login-page">
        <div className="login-container">
          <h1 className="login-title">Poulomi & Subhayan</h1>
          <Authenticator hideSignUp />
        </div>
      </div>
    );
  }

  return (
    <main className="app-container">
      <header className="app-header">
        <div className="header-left">
          <button type="button" className="back-btn" onClick={() => { window.location.href = '/'; }}>← Home</button>
          <h1>Daily Assist — German Flashcards</h1>
        </div>
        <div className="user-info">
          <span>{authEnabled ? `Welcome, ${user?.signInDetails?.loginId}` : 'Local dev mode'}</span>
          {authEnabled && <button type="button" onClick={signOut} className="sign-out-btn">Sign Out</button>}
        </div>
      </header>
      <LanguageLearningApp />
    </main>
  );
}

function App() {
  return (
    <Authenticator.Provider>
      <AppContent />
    </Authenticator.Provider>
  );
}

export default App;
