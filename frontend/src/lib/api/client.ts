import axios from 'axios';
import { useAuth } from '@/store/useAuth';

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

export const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/** Extract a human-readable error message from API error responses */
export function getApiErrorMessage(error: unknown, fallback = 'Something went wrong'): string {
  const err = error as { response?: { data?: { detail?: unknown; message?: string } } };
  const detail = err.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((e: { msg?: string; loc?: unknown[] }) =>
        e.loc?.length ? `${e.loc[e.loc.length - 1]}: ${e.msg}` : e.msg
      )
      .filter(Boolean)
      .join(', ');
  }
  if (err.response?.data?.message) return err.response.data.message;
  return fallback;
}

apiClient.interceptors.request.use(
  (config) => {
    const token = useAuth.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      // Read refresh token from sessionStorage via the store action
      const refreshToken = useAuth.getState().rehydrateTokens();

      if (refreshToken) {
        try {
          const res = await axios.post(`${apiClient.defaults.baseURL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });

          if (res.data?.access_token) {
            useAuth.getState().setTokens(res.data.access_token, res.data.refresh_token);
            originalRequest.headers.Authorization = `Bearer ${res.data.access_token}`;
            return apiClient(originalRequest);
          }
        } catch {
          // Refresh failed — force logout
          useAuth.getState().logout();
          if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
            window.location.href = '/login';
          }
          return Promise.reject(error);
        }
      } else {
        useAuth.getState().logout();
        if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }
      }
    }

    return Promise.reject(error);
  }
);

