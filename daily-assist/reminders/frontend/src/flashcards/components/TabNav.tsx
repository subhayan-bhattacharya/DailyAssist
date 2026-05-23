export type AppTab = 'review' | 'search' | 'add-word' | 'settings' | 'prompt';

interface TabNavProps {
  activeTab: AppTab;
  onChange: (tab: AppTab) => void;
}

const tabs: Array<{ id: AppTab; label: string }> = [
  { id: 'review', label: 'Review' },
  { id: 'search', label: 'Search' },
  { id: 'add-word', label: 'Add Word' },
  { id: 'settings', label: 'Settings' },
  { id: 'prompt', label: 'Prompt' },
];

export function TabNav({ activeTab, onChange }: TabNavProps) {
  return (
    <nav className="tab-nav" aria-label="Language learning sections">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => onChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  );
}
