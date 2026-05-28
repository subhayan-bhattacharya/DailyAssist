/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_COGNITO_USER_POOL_ID?: string;
  readonly VITE_COGNITO_CLIENT_ID?: string;
  readonly VITE_API_URL?: string;
  readonly VITE_FLASHCARDS_API_URL?: string;
  readonly VITE_LANGUAGE_API_URL?: string;
  readonly VITE_AUTH_ENABLED?: string;
  readonly VITE_MOCK_API?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
