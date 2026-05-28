import { useEffect } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Authenticator, useAuthenticator } from '@aws-amplify/ui-react';
import { authEnabled } from '../../shared/frontend/auth';
import { RemindersList } from '../../reminders/frontend/src/components/RemindersList';
import { LanguageLearningApp } from '../../language-learning/frontend/src/components/LanguageLearningApp';
import { AppHeader } from './shell/AppHeader';
import { AppSelector } from './shell/AppSelector';
import { LoginPage } from './shell/LoginPage';

function AppRoutes() {
  const { route, signOut, skipVerification, user } = useAuthenticator((context) => [
    context.route,
    context.user,
  ]);

  useEffect(() => {
    if (route === 'verifyUser') skipVerification();
  }, [route, skipVerification]);

  if (authEnabled && route !== 'authenticated') {
    return <LoginPage />;
  }

  return (
    <main className="app-container">
      <AppHeader user={user} isAuthEnabled={authEnabled} signOut={signOut} />
      <Routes>
        <Route path="/" element={<AppSelector />} />
        <Route path="/reminders/*" element={<RemindersList />} />
        <Route path="/flashcards/*" element={<LanguageLearningApp />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </main>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Authenticator.Provider>
        <AppRoutes />
      </Authenticator.Provider>
    </BrowserRouter>
  );
}

export default App;
