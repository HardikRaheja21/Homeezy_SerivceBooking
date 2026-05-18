import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuth } from '@/store/useAuth';
import { toast } from 'sonner';
import { emitDashboardRefresh } from '@/lib/realtime-events';

interface WebSocketMessage {
  type: string;
  message?: string;
  booking_id?: string;
  data?: unknown;
}

export function useWebSocket(options?: { enablePollingFallback?: boolean }) {
  const { accessToken, isAuthenticated } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout>>();
  const pollInterval = useRef<ReturnType<typeof setInterval>>();

  const handleMessage = useCallback((msg: WebSocketMessage) => {
    switch (msg.type) {
      case 'system':
        break;
      case 'BOOKING_CREATED':
      case 'BOOKING_UPDATE':
      case 'NEW_REQUEST':
        if (msg.message) toast.info(msg.message);
        emitDashboardRefresh();
        break;
      case 'WORKER_APPROVED':
        toast.success(msg.message || 'Worker status updated');
        emitDashboardRefresh();
        break;
      default:
        break;
    }
  }, []);

  const connect = useCallback(() => {
    if (!isAuthenticated || !accessToken) return;

    const apiUrl = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');
    const wsProtocol = apiUrl.startsWith('https') ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${apiUrl.replace(/^https?:\/\//, '')}/ws?token=${accessToken}`;

    try {
      ws.current = new WebSocket(wsUrl);
    } catch {
      return;
    }

    ws.current.onopen = () => {
      setIsConnected(true);
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
      if (pollInterval.current) {
        clearInterval(pollInterval.current);
        pollInterval.current = undefined;
      }
    };

    ws.current.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        handleMessage(data);
      } catch {
        /* ignore */
      }
    };

    ws.current.onclose = (event) => {
      setIsConnected(false);
      if (event.code === 1008 || event.code === 1003 || event.code === 4001) {
        useAuth.getState().logout();
        if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }
        return;
      }
      reconnectTimeout.current = setTimeout(connect, 4000);
    };

    ws.current.onerror = () => {
      ws.current?.close();
    };
  }, [accessToken, isAuthenticated, handleMessage]);

  useEffect(() => {
    connect();
    if (options?.enablePollingFallback !== false && isAuthenticated) {
      pollInterval.current = setInterval(() => emitDashboardRefresh(), 60000);
    }
    return () => {
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
      if (pollInterval.current) clearInterval(pollInterval.current);
      ws.current?.close();
    };
  }, [connect, isAuthenticated, options?.enablePollingFallback]);

  const joinBookingRoom = (bookingId: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ action: 'join_booking', booking_id: bookingId }));
    }
  };

  const leaveBookingRoom = (bookingId: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ action: 'leave_booking', booking_id: bookingId }));
    }
  };

  return { isConnected, joinBookingRoom, leaveBookingRoom };
}
