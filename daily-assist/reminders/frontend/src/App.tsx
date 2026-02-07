import { useEffect } from 'react';
import { Authenticator, useAuthenticator } from '@aws-amplify/ui-react';
import { RemindersList } from './components/RemindersList';
import './App.css';

function AppContent() {
  const { route, signOut, user, skipVerification } = useAuthenticator();

  useEffect(() => {
    if (route === 'verifyUser') {
      skipVerification();
    }
  }, [route, skipVerification]);

  if (route !== 'authenticated') {
    return <Authenticator hideSignUp />;
  }

  return (
    <main className="app-container">
      <header className="app-header">
        <h1>Daily Assist - Reminders</h1>
        <div className="user-info">
          <span>Welcome, {user?.signInDetails?.loginId}</span>
          <button onClick={signOut} className="sign-out-btn">Sign Out</button>
        </div>
      </header>
      <RemindersList />
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
