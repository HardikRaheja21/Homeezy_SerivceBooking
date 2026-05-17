import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuth } from '@/store/useAuth';
import { toast } from 'sonner';

interface WebSocketMessage {
  type: string;
  message?: string;
  data?: any;
}

export function useWebSocket() {
  const { accessToken, isAuthenticated } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    if (!isAuthenticated || !accessToken) return;

    // Determine WS URL from API URL
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const wsProtocol = apiUrl.startsWith('https') ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${apiUrl.replace(/^https?:\/\//, '')}/ws?token=${accessToken}`;

    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
    };

    ws.current.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        handleMessage(data);
      } catch (err) {
        console.error('Failed to parse WebSocket message', err);
      }
    };

    ws.current.onclose = (event) => {
      console.log(`WebSocket disconnected (code: ${event.code})`);
      setIsConnected(false);
      
      // Do not reconnect if the server explicitly rejected auth
      if (event.code === 1008 || event.code === 1003 || event.code === 4001) {
        console.error('WebSocket auth failed. Logging out.');
        useAuth.getState().logout();
        if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }
        return;
      }

      // Reconnect with exponential backoff (simplified here to 3s)
      reconnectTimeout.current = setTimeout(connect, 3000);
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error', error);
      ws.current?.close();
    };
  }, [accessToken, isAuthenticated]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

  const handleMessage = (msg: WebSocketMessage) => {
    switch (msg.type) {
      case 'system':
        console.log('System message:', msg.message);
        break;
      case 'BOOKING_UPDATE':
        toast.info(`Booking Update: ${msg.message}`);
        // Optionally trigger a re-fetch of data
        break;
      case 'NEW_REQUEST':
        toast.success(`New Job Request: ${msg.message}`);
        break;
      default:
        console.log('Received:', msg);
    }
  };

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
