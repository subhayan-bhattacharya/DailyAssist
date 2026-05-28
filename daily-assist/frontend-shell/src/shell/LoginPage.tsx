import { Authenticator } from '@aws-amplify/ui-react';

export function LoginPage() {
  return (
    <main className="login-page">
      <div className="login-container">
        <p className="login-eyebrow">Daily Assist</p>
        <h1 className="login-title">Poulomi & Subhayan</h1>
        <Authenticator hideSignUp />
      </div>
    </main>
  );
}
