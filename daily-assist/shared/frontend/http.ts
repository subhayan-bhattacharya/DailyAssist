import { authEnabled, getAuthToken, getRequiredAuthToken } from './auth';

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

interface RequestJsonOptions extends RequestInit {
  requireAuth?: boolean;
}

export async function requestJson<T>(
  baseUrl: string,
  path: string,
  options: RequestJsonOptions = {}
): Promise<T> {
  const { requireAuth = true, ...fetchOptions } = options;
  const token = requireAuth && authEnabled ? await getRequiredAuthToken() : await getAuthToken();
  const headers = new Headers(fetchOptions.headers);

  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  if (token) {
    headers.set('Authorization', token);
  }

  const response = await fetch(`${baseUrl}${path}`, { ...fetchOptions, headers });

  if (!response.ok) {
    const text = await response.text();
    throw new ApiError(text || `Request failed with status ${response.status}`, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}
