'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';
import { Loader2 } from 'lucide-react';
import { useAuth } from '@/store/useAuth';
import { apiClient } from '@/lib/api/client';

/**
 * Restores access token from session refresh token on mount so API calls work after page reload.
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuth((s) => s.isAuthenticated);
  const accessToken = useAuth((s) => s.accessToken);
  const rehydrateTokens = useAuth((s) => s.rehydrateTokens);
  const setTokens = useAuth((s) => s.setTokens);
  const setAuth = useAuth((s) => s.setAuth);
  const logout = useAuth((s) => s.logout);
  const user = useAuth((s) => s.user);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      if (!isAuthenticated) {
        setReady(true);
        return;
      }

      const refreshToken = rehydrateTokens();
      if (!refreshToken) {
        logout();
        setReady(true);
        return;
      }

      if (!accessToken) {
        try {
          const baseURL = apiClient.defaults.baseURL;
          const res = await axios.post(`${baseURL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });
          if (cancelled) return;
          if (res.data?.access_token) {
            setTokens(res.data.access_token, res.data.refresh_token);
          } else {
            logout();
            setReady(true);
            return;
          }
        } catch {
          if (!cancelled) logout();
          setReady(true);
          return;
        }
      }

      try {
        const meRes = await apiClient.get('/api/v1/users/me');
        if (cancelled) return;
        const me = meRes.data;
        const role = typeof me.role === 'string' ? me.role : me.role?.value ?? user?.role;
        const token = useAuth.getState().accessToken;
        if (user && me && token) {
          setAuth(
            {
              ...user,
              id: me.id ?? user.id,
              email: me.email ?? user.email,
              full_name: me.full_name ?? user.full_name,
              role: role as typeof user.role,
              phone: me.phone,
              account_status:
                typeof me.account_status === 'string'
                  ? me.account_status
                  : me.account_status?.value,
              profile_photo: me.profile_photo,
            },
            token,
            refreshToken
          );
        }
      } catch {
        // Profile sync failed — keep existing persisted user if tokens are valid
      }

      if (!cancelled) setReady(true);
    }

    bootstrap();
    return () => {
      cancelled = true;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps -- run once on mount

  if (!ready) {
    return (
      <div className="flex flex-1 items-center justify-center min-h-[40vh]" aria-busy="true" aria-label="Loading session">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
      </div>
    );
  }

  return <>{children}</>;
}
