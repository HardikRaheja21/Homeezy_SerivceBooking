type RefreshListener = () => void;

const listeners = new Set<RefreshListener>();

export function onDashboardRefresh(listener: RefreshListener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function emitDashboardRefresh(): void {
  listeners.forEach((fn) => {
    try {
      fn();
    } catch (e) {
      console.error('Dashboard refresh listener error', e);
    }
  });
}
