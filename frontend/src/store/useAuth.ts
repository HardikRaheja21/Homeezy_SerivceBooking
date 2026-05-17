import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

export type UserRole = 'customer' | 'worker' | 'admin';

export interface User {
  id?: string;
  email: string;
  full_name: string;
  role: UserRole;
  phone?: string;
  account_status?: string;
  profile_photo?: string | null;
}

interface AuthState {
  user: User | null;
  // accessToken is NOT persisted — lives in memory only (cleared on tab close)
  accessToken: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, accessToken: string, refreshToken: string) => void;
  setTokens: (accessToken: string, refreshToken?: string) => void;
  logout: () => void;
  // Called on app mount to restore session from sessionStorage
  rehydrateTokens: () => string | null;
}

// Key for sessionStorage — tab-scoped, not accessible by cross-origin scripts
const SESSION_REFRESH_KEY = 'homeezy_refresh';

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      isAuthenticated: false,

      setAuth: (user, accessToken, refreshToken) => {
        // Persist refresh token to sessionStorage (tab-scoped, not localStorage)
        if (typeof window !== 'undefined') {
          window.sessionStorage.setItem(SESSION_REFRESH_KEY, refreshToken);
          document.cookie = `homeezy_auth=true; path=/; max-age=86400; SameSite=Strict`;
          document.cookie = `homeezy_role=${user.role}; path=/; max-age=86400; SameSite=Strict`;
        }
        // accessToken lives in memory (Zustand state) — not persisted
        set({ user, accessToken, isAuthenticated: true });
      },

      setTokens: (accessToken, refreshToken) => {
        if (refreshToken && typeof window !== 'undefined') {
          window.sessionStorage.setItem(SESSION_REFRESH_KEY, refreshToken);
        }
        set((state) => ({ ...state, accessToken }));
      },

      rehydrateTokens: () => {
        if (typeof window === 'undefined') return null;
        return window.sessionStorage.getItem(SESSION_REFRESH_KEY);
      },

      logout: () => {
        if (typeof window !== 'undefined') {
          window.sessionStorage.removeItem(SESSION_REFRESH_KEY);
          document.cookie = 'homeezy_auth=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Strict';
          document.cookie = 'homeezy_role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Strict';
        }
        set({ user: null, accessToken: null, isAuthenticated: false });
      },
    }),
    {
      name: 'homeezy-auth-storage',
      storage: createJSONStorage(() => localStorage),
      // Only persist the user profile — NOT the accessToken (security fix)
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);

