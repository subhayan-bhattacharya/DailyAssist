import { useNavigate } from 'react-router-dom';

export function AppSelector() {
  const navigate = useNavigate();

  return (
    <section className="selector-page" aria-labelledby="selector-heading">
      <div className="selector-intro">
        <p className="eyebrow">Choose an app</p>
        <h2 id="selector-heading">What would you like to do?</h2>
        <p>Use the same login for reminders and German practice.</p>
      </div>
      <div className="selector-grid">
        <button type="button" className="app-card" onClick={() => navigate('/reminders')}>
          <span className="app-card-icon" aria-hidden="true">R</span>
          <span className="app-card-title">Reminders</span>
          <span className="app-card-copy">View and manage your personal reminders.</span>
        </button>
        <button type="button" className="app-card" onClick={() => navigate('/flashcards')}>
          <span className="app-card-icon" aria-hidden="true">DE</span>
          <span className="app-card-title">German Flashcards</span>
          <span className="app-card-copy">Practice vocabulary with daily review sessions.</span>
        </button>
      </div>
    </section>
  );
}
