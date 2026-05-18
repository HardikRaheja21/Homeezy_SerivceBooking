import { useEffect } from 'react';
import { onDashboardRefresh } from '@/lib/realtime-events';

/** Refetch dashboard data when realtime events or WebSocket messages fire */
export function useDashboardSync(refetch: () => void, pollMs = 0) {
  useEffect(() => {
    const unsub = onDashboardRefresh(refetch);
    let interval: ReturnType<typeof setInterval> | undefined;
    if (pollMs > 0) {
      interval = setInterval(refetch, pollMs);
    }
    return () => {
      unsub();
      if (interval) clearInterval(interval);
    };
  }, [refetch, pollMs]);
}
