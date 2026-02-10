import { fetchAuthSession } from 'aws-amplify/auth';

export async function getAuthToken(): Promise<string> {
  const session = await fetchAuthSession();
  const token = session.tokens?.idToken?.toString();
  if (!token) {
    throw new Error('No authentication token available');
  }
  return token;
}
