import { useNavigate } from 'react-router-dom';
import './AppSelector.css';

export function AppSelector() {
  const navigate = useNavigate();

  return (
    <div className="selector-page">
      <h2 className="selector-heading">What would you like to do?</h2>
      <div className="selector-grid">
        <button className="app-card" onClick={() => navigate('/reminders')}>
          <span className="app-card-icon">🔔</span>
          <h3>Reminders</h3>
          <p>View and manage your personal reminders</p>
        </button>
        <button className="app-card" onClick={() => navigate('/flashcards')}>
          <span className="app-card-icon">🇩🇪</span>
          <h3>German Flashcards</h3>
          <p>Practice vocabulary with daily flashcard sessions</p>
        </button>
      </div>
    </div>
  );
}
