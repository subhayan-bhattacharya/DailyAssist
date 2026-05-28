import { useLocation, useNavigate } from 'react-router-dom';
import type { AuthUser } from 'aws-amplify/auth';

interface AppHeaderProps {
  user?: AuthUser;
  isAuthEnabled: boolean;
  signOut?: () => void;
}

const routeTitles: Record<string, string> = {
  '/': 'Daily Assist',
  '/reminders': 'Daily Assist - Reminders',
  '/flashcards': 'Daily Assist - German Flashcards',
};

function getTitle(pathname: string): string {
  if (pathname.startsWith('/reminders')) {
    return routeTitles['/reminders'];
  }

  if (pathname.startsWith('/flashcards')) {
    return routeTitles['/flashcards'];
  }

  return routeTitles['/'];
}

export function AppHeader({ user, isAuthEnabled, signOut }: AppHeaderProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const isHome = location.pathname === '/';
  const loginId = user?.signInDetails?.loginId;

  return (
    <header className="app-header">
      <div className="header-left">
        {!isHome && (
          <button type="button" className="back-btn" onClick={() => navigate('/')}>
            Home
          </button>
        )}
        <div>
          <p className="app-kicker">Poulomi & Subhayan</p>
          <h1>{getTitle(location.pathname)}</h1>
        </div>
      </div>
      <div className="user-info">
        <span>{isAuthEnabled ? `Welcome, ${loginId ?? 'friend'}` : 'Local dev mode'}</span>
        {isAuthEnabled && (
          <button type="button" onClick={signOut} className="sign-out-btn">
            Sign Out
          </button>
        )}
      </div>
    </header>
  );
}
