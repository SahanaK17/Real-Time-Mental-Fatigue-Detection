/**
 * WebSocket Hook
 * Real-time fatigue score updates via WebSocket
 * 
 * Fixed: exponential backoff, max retries, stable refs to prevent
 * infinite reconnect loop when backend is unavailable.
 */
import { useEffect, useRef, useCallback, useState } from 'react';
import type { WsMessage } from '@/types';

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 
  (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host;


const MAX_RECONNECTS = 5;
const BASE_DELAY_MS = 3000; // 3s, 6s, 12s, 24s, 48s

interface UseWebSocketOptions {
  userId: string | null;
  enabled?: boolean;
  onMessage?: (msg: WsMessage) => void;
}

export function useWebSocket({
  userId,
  enabled = true,
  onMessage,
}: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCount = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMounted = useRef(true);
  const onMessageRef = useRef(onMessage);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WsMessage | null>(null);

  // Keep onMessage ref up to date without triggering reconnects
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  const scheduleReconnect = useCallback(() => {
    if (!isMounted.current) return;
    if (reconnectCount.current >= MAX_RECONNECTS) {
      console.warn('[WS] Max reconnects reached, giving up.');
      return;
    }
    const delay = BASE_DELAY_MS * Math.pow(2, reconnectCount.current);
    reconnectCount.current++;
    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${reconnectCount.current}/${MAX_RECONNECTS})...`);
    reconnectTimer.current = setTimeout(() => {
      if (isMounted.current) connectInternal();
    }, delay);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const connectInternal = useCallback(() => {
    if (!isMounted.current) return;

    const token = localStorage.getItem('access_token');
    if (!token || !userId) return;

    // Close existing connection if any
    if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) {
      wsRef.current.onclose = null; // prevent triggering reconnect
      wsRef.current.close();
    }

    const url = `${WS_BASE_URL}/ws/${userId}?token=${token}`;
    let pingInterval: ReturnType<typeof setInterval> | null = null;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!isMounted.current) { ws.close(); return; }
        setIsConnected(true);
        reconnectCount.current = 0;
        console.log('[WS] Connected');
        pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) ws.send('ping');
        }, 30000);
      };

      ws.onmessage = (event) => {
        if (event.data === 'pong') return;
        try {
          const msg = JSON.parse(event.data) as WsMessage;
          setLastMessage(msg);
          onMessageRef.current?.(msg);
        } catch {
          console.warn('[WS] Failed to parse message:', event.data);
        }
      };

      ws.onerror = () => {
        // onerror is always followed by onclose — let onclose handle reconnect
      };

      ws.onclose = (event) => {
        if (pingInterval) clearInterval(pingInterval);
        if (!isMounted.current) return;
        setIsConnected(false);
        console.log(`[WS] Closed (code=${event.code})`);
        // Don't reconnect on clean close (1000) or auth failure (4001/4003)
        if (event.code === 1000 || event.code === 4001 || event.code === 4003) return;
        scheduleReconnect();
      };
    } catch (error) {
      console.error('[WS] Failed to create connection:', error);
      scheduleReconnect();
    }
  }, [userId, scheduleReconnect]);

  // Only connect when userId and enabled change
  useEffect(() => {
    isMounted.current = true;
    if (enabled && userId) {
      reconnectCount.current = 0;
      connectInternal();
    }
    return () => {
      isMounted.current = false;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (wsRef.current) {
        wsRef.current.onclose = null; // prevent reconnect on cleanup
        wsRef.current.close(1000, 'Component unmounted');
        wsRef.current = null;
      }
      setIsConnected(false);
    };
  }, [userId, enabled]); // eslint-disable-line react-hooks/exhaustive-deps

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
    reconnectCount.current = MAX_RECONNECTS; // prevent further reconnects
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  return { isConnected, lastMessage, disconnect, reconnect: connectInternal };
}
