import { Authenticator } from '@aws-amplify/ui-react';
import { RemindersList } from './components/RemindersList';
import './App.css';

function App() {
  return (
    <Authenticator>
      {({ signOut, user }) => (
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
      )}
    </Authenticator>
  );
}

export default App;
