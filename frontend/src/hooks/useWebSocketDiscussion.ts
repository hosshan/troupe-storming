import { useState, useEffect, useRef, useCallback } from 'react';

interface DiscussionMessage {
  speaker: string;
  content: string;
  timestamp: string;
}

interface WebSocketData {
  progress: number;
  message: string;
  completed: boolean;
  error?: string;
  messages?: DiscussionMessage[];
}

interface UseWebSocketDiscussionOptions {
  discussionId: number;
  onProgress?: (data: WebSocketData) => void;
  onComplete?: (messages: DiscussionMessage[]) => void;
  onError?: (error: string) => void;
  autoConnect?: boolean;
}

export const useWebSocketDiscussion = ({
  discussionId,
  onProgress,
  onComplete,
  onError,
  autoConnect = true,
}: UseWebSocketDiscussionOptions) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');
  const [messages, setMessages] = useState<DiscussionMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isCompleted, setIsCompleted] = useState(false);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    setIsConnecting(true);
    setError(null);

    const wsUrl = `ws://localhost:8000/ws/discussions/${discussionId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log(`WebSocket connected to discussion ${discussionId}`);
      setIsConnected(true);
      setIsConnecting(false);
      reconnectAttempts.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const data: WebSocketData = JSON.parse(event.data);
        
        setProgress(data.progress);
        setProgressMessage(data.message);
        
        if (data.messages) {
          setMessages(data.messages);
        }
        
        if (data.error) {
          setError(data.error);
          onError?.(data.error);
        }
        
        if (data.completed) {
          setIsCompleted(true);
          if (data.messages && !data.error) {
            onComplete?.(data.messages);
          }
        }
        
        onProgress?.(data);
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
        setError('メッセージの解析に失敗しました');
      }
    };

    ws.onclose = (event) => {
      console.log(`WebSocket closed for discussion ${discussionId}:`, event.code, event.reason);
      setIsConnected(false);
      setIsConnecting(false);
      
      // Attempt to reconnect if not completed and within retry limit
      if (!isCompleted && reconnectAttempts.current < maxReconnectAttempts) {
        reconnectAttempts.current++;
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000); // Exponential backoff
        
        console.log(`Attempting to reconnect in ${delay}ms (attempt ${reconnectAttempts.current}/${maxReconnectAttempts})`);
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      } else if (reconnectAttempts.current >= maxReconnectAttempts) {
        setError('接続に失敗しました。再試行回数を超えました。');
        onError?.('接続に失敗しました。再試行回数を超えました。');
      }
    };

    ws.onerror = (error) => {
      console.error(`WebSocket error for discussion ${discussionId}:`, error);
      setError('WebSocket接続でエラーが発生しました');
    };
  }, [discussionId, isCompleted, onProgress, onComplete, onError]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
    setIsConnecting(false);
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  return {
    // Connection state
    isConnected,
    isConnecting,
    connect,
    disconnect,
    sendMessage,
    
    // Discussion state
    progress,
    progressMessage,
    messages,
    error,
    isCompleted,
    
    // Actions
    retry: connect,
  };
};