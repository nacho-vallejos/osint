'use client';

import { useEffect, useState, useRef, useCallback } from 'react';

/**
 * Message types from WebSocket
 */
export type ScanSocketMessageType = 
  | 'connection' 
  | 'task_started' 
  | 'task_progress' 
  | 'task_complete' 
  | 'task_failed' 
  | 'task_error' 
  | 'task_retry'
  | 'pong';

/**
 * WebSocket message structure
 */
export interface ScanSocketMessage {
  type: ScanSocketMessageType;
  status?: 'STARTED' | 'PROCESSING' | 'SUCCESS' | 'FAILURE' | 'RETRY';
  task_id?: string;
  collector_type?: string;
  target?: string;
  message?: string;
  progress?: number;
  result?: any;
  error?: string;
  retry_count?: number;
}

/**
 * Hook state and controls
 */
export interface UseScanSocketReturn {
  /** Last message received from WebSocket */
  lastMessage: ScanSocketMessage | null;
  
  /** Current connection status */
  status: 'disconnected' | 'connecting' | 'connected' | 'error';
  
  /** Whether WebSocket is currently connected */
  isConnected: boolean;
  
  /** Error message if connection failed */
  error: string | null;
  
  /** Progress percentage (0-100) if available */
  progress: number;
  
  /** Manually close the connection */
  disconnect: () => void;
  
  /** Manually reconnect */
  reconnect: () => void;
  
  /** All messages received (history) */
  messages: ScanSocketMessage[];
}

/**
 * Custom React Hook for WebSocket-based OSINT scan updates.
 * 
 * Connects to the FastAPI WebSocket endpoint and receives real-time updates
 * about scan progress and results, eliminating the need for polling.
 * 
 * @param taskId - The Celery task ID to monitor. Pass null to not connect.
 * @param options - Configuration options
 * @returns Hook state and control functions
 * 
 * @example
 * ```tsx
 * const { lastMessage, status, isConnected, progress } = useScanSocket(taskId);
 * 
 * useEffect(() => {
 *   if (lastMessage?.status === 'SUCCESS') {
 *     console.log('Scan complete:', lastMessage.result);
 *   }
 * }, [lastMessage]);
 * ```
 */
export function useScanSocket(
  taskId: string | null,
  options?: {
    /** Base WebSocket URL (default: auto-detect from window.location) */
    wsUrl?: string;
    /** Auto-reconnect on error (default: false) */
    autoReconnect?: boolean;
    /** Auto-close on completion (default: true) */
    autoCloseOnComplete?: boolean;
  }
): UseScanSocketReturn {
  const {
    wsUrl,
    autoReconnect = false,
    autoCloseOnComplete = true,
  } = options || {};

  // State
  const [lastMessage, setLastMessage] = useState<ScanSocketMessage | null>(null);
  const [messages, setMessages] = useState<ScanSocketMessage[]>([]);
  const [status, setStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);

  // Refs to avoid stale closures
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const taskIdRef = useRef<string | null>(taskId);

  // Update taskIdRef when taskId changes
  useEffect(() => {
    taskIdRef.current = taskId;
  }, [taskId]);

  /**
   * Construct WebSocket URL
   */
  const getWebSocketUrl = useCallback(() => {
    if (wsUrl) {
      return wsUrl;
    }

    // Auto-detect from browser location
    if (typeof window !== 'undefined') {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      
      // For development, assume backend is on port 8000
      const backendHost = process.env.NODE_ENV === 'development' 
        ? 'localhost:8000' 
        : host;
      
      return `${protocol}//${backendHost}/ws/scan/${taskIdRef.current}`;
    }

    return null;
  }, [wsUrl]);

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(() => {
    if (!taskIdRef.current) {
      return;
    }

    if (wsRef.current) {
      // Already connected or connecting
      return;
    }

    const url = getWebSocketUrl();
    if (!url) {
      setError('Failed to determine WebSocket URL');
      setStatus('error');
      return;
    }

    try {
      setStatus('connecting');
      setError(null);

      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[useScanSocket] WebSocket connected:', taskIdRef.current);
        setStatus('connected');
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const data: ScanSocketMessage = JSON.parse(event.data);
          console.log('[useScanSocket] Message received:', data);

          // Update state
          setLastMessage(data);
          setMessages((prev) => [...prev, data]);

          // Update progress if available
          if (typeof data.progress === 'number') {
            setProgress(data.progress);
          }

          // Handle completion
          if (data.status === 'SUCCESS' || data.status === 'FAILURE') {
            setProgress(100);
            
            if (autoCloseOnComplete) {
              console.log('[useScanSocket] Scan complete, auto-closing...');
              setTimeout(() => {
                ws.close();
              }, 1000);
            }
          }
        } catch (err) {
          console.error('[useScanSocket] Failed to parse message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('[useScanSocket] WebSocket error:', event);
        setError('WebSocket connection error');
        setStatus('error');
      };

      ws.onclose = (event) => {
        console.log('[useScanSocket] WebSocket closed:', event.code, event.reason);
        wsRef.current = null;
        setStatus('disconnected');

        // Auto-reconnect if enabled and not a normal closure
        if (autoReconnect && event.code !== 1000 && taskIdRef.current) {
          console.log('[useScanSocket] Auto-reconnecting in 3 seconds...');
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, 3000);
        }
      };
    } catch (err) {
      console.error('[useScanSocket] Failed to create WebSocket:', err);
      setError('Failed to create WebSocket connection');
      setStatus('error');
      wsRef.current = null;
    }
  }, [getWebSocketUrl, autoReconnect, autoCloseOnComplete]);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setStatus('disconnected');
  }, []);

  /**
   * Reconnect to WebSocket
   */
  const reconnect = useCallback(() => {
    disconnect();
    setTimeout(() => {
      connect();
    }, 100);
  }, [connect, disconnect]);

  /**
   * Effect: Connect when taskId is provided
   */
  useEffect(() => {
    if (taskId) {
      connect();
    } else {
      disconnect();
    }

    // Cleanup on unmount or taskId change
    return () => {
      disconnect();
    };
  }, [taskId]); // Only depend on taskId

  return {
    lastMessage,
    status,
    isConnected: status === 'connected',
    error,
    progress,
    disconnect,
    reconnect,
    messages,
  };
}
