import { fetchAuthSession } from 'aws-amplify/auth';

export const authEnabled = true;

export async function getAuthToken(): Promise<string | null> {
  const session = await fetchAuthSession();
  return session.tokens?.idToken?.toString() ?? null;
}
