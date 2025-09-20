import { useEffect, useRef, useState, useCallback } from 'react';

export interface Action {
  timestamp: number;
  action: string;
  detail: string;
  status: 'running' | 'completed' | 'failed';
  source?: string;
}

export interface AnalysisResult {
  summary: string;
  risk_report: string;
  output: string;
  voice_url: string;
}

interface UseSSEConnectionProps {
  onAction?: (action: Action) => void;
  onComplete?: (result: AnalysisResult) => void;
  onError?: (error: string) => void;
}

export const useSSEConnection = ({
  onAction,
  onComplete,
  onError,
}: UseSSEConnectionProps = {}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>();
  const retryCountRef = useRef(0);
  const MAX_RETRIES = 3;
  const RETRY_DELAY = 2000;

  const isMessageEvent = (event: Event): event is MessageEvent<string> => {
    return typeof (event as MessageEvent<string>).data === 'string';
  };

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
  }, []);

  const connect = useCallback((prompt: string) => {
    disconnect();
    setIsLoading(true);
    retryCountRef.current = 0;

    const apiUrl = (window as any).REACT_APP_API_URL || 'http://localhost:8000';
    const url = `${apiUrl}/prompt?message=${encodeURIComponent(prompt)}`;

    const createConnection = () => {
      const source = new EventSource(url);
      eventSourceRef.current = source;

      source.onopen = () => {
        setIsConnected(true);
        retryCountRef.current = 0;
      };

      source.addEventListener('action', (event) => {
        try {
          const action = JSON.parse(event.data);
          onAction?.(action);
        } catch (err) {
          console.error('Failed to parse action:', err);
        }
      });

      source.addEventListener('complete', (event) => {
        try {
          const data = JSON.parse(event.data);
          onComplete?.(data);
        } catch (err) {
          console.error('Failed to parse complete event:', err);
          onError?.('Failed to parse response');
        } finally {
          setIsLoading(false);
          disconnect();
        }
      });

      const handleNetworkFailure = () => {
        setIsConnected(false);

        if (retryCountRef.current < MAX_RETRIES) {
          retryCountRef.current++;
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`Retrying connection (${retryCountRef.current}/${MAX_RETRIES})...`);
            createConnection();
          }, RETRY_DELAY * retryCountRef.current);
        } else {
          onError?.('Connection failed after maximum retries');
          setIsLoading(false);
          disconnect();
        }
      };

      const handleErrorEvent = (event: Event) => {
        console.error('SSE connection error:', event);

        if (isMessageEvent(event) && event.data) {
          try {
            const payload = JSON.parse(event.data);
            const detail = typeof payload?.detail === 'string'
              ? payload.detail
              : 'Streaming error';
            onError?.(detail);
          } catch (err) {
            console.error('Failed to parse error event:', err);
            onError?.('Streaming connection error');
          } finally {
            setIsLoading(false);
            disconnect();
          }
          return;
        }

        handleNetworkFailure();
      };

      source.addEventListener('error', handleErrorEvent as EventListener);
    };

    createConnection();
  }, [disconnect, onAction, onComplete, onError]);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    connect,
    disconnect,
    isConnected,
    isLoading,
  };
};
