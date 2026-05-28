import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import '../../shared/frontend/amplify-config';
import '@aws-amplify/ui-react/styles.css';
import './styles/index.css';
import App from './App';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
