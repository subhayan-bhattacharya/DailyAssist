import { fetchAuthSession } from 'aws-amplify/auth';
import { authConfigured } from '../amplify-config';

export const authEnabled = authConfigured && import.meta.env.VITE_AUTH_ENABLED !== 'false';

export async function getAuthToken(): Promise<string | null> {
  if (!authEnabled) {
    return null;
  }

  const session = await fetchAuthSession();
  const token = session.tokens?.idToken?.toString();

  if (!token) {
    throw new Error('No authentication token available');
  }

  return token;
}
