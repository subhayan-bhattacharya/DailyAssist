import { useState } from 'react';
import { AddWordForm } from './AddWordForm';
import { FlashcardReview } from './FlashcardReview';
import { PromptEditor } from './PromptEditor';
import { SettingsPanel } from './SettingsPanel';
import { TabNav, type AppTab } from './TabNav';
import { WordSearch } from './WordSearch';

export function LanguageLearningApp() {
  const [activeTab, setActiveTab] = useState<AppTab>('review');

  return (
    <section className="app-surface">
      <div className="surface-header">
        <div>
          <p className="eyebrow">German B2 Practice</p>
          <h2>Flashcards</h2>
        </div>
        <span className="api-chip">Daily Assist</span>
      </div>

      <TabNav activeTab={activeTab} onChange={setActiveTab} />

      <div className="tab-content">
        {activeTab === 'review' && <FlashcardReview />}
        {activeTab === 'search' && <WordSearch />}
        {activeTab === 'add-word' && <AddWordForm />}
        {activeTab === 'settings' && <SettingsPanel />}
        {activeTab === 'prompt' && <PromptEditor />}
      </div>
    </section>
  );
}
