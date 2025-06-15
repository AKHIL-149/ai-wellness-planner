// frontend/src/hooks/useWebSocket.js

import { useState, useEffect, useRef, useCallback } from 'react';

export const useWebSocket = (url, options = {}) => {
  const [socket, setSocket] = useState(null);
  const [lastMessage, setLastMessage] = useState(null);
  const [readyState, setReadyState] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('Uninstantiated');

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);

  const {
    onOpen,
    onClose,
    onMessage,
    onError,
    shouldReconnect = true,
    reconnectAttempts = 5,
    reconnectInterval = 3000,
  } = options;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      wsRef.current = new WebSocket(url);
      setSocket(wsRef.current);
      setConnectionStatus('Connecting');

      wsRef.current.onopen = (event) => {
        setReadyState(WebSocket.OPEN);
        setConnectionStatus('Open');
        reconnectAttemptsRef.current = 0;
        onOpen?.(event);
      };

      wsRef.current.onclose = (event) => {
        setReadyState(WebSocket.CLOSED);
        setConnectionStatus('Closed');
        onClose?.(event);

        if (shouldReconnect && reconnectAttemptsRef.current < reconnectAttempts) {
          reconnectAttemptsRef.current++;
          setConnectionStatus(`Reconnecting (${reconnectAttemptsRef.current}/${reconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

      wsRef.current.onmessage = (event) => {
        setLastMessage(event);
        onMessage?.(event);
      };

      wsRef.current.onerror = (event) => {
        setConnectionStatus('Error');
        onError?.(event);
      };

    } catch (error) {
      setConnectionStatus('Error');
      onError?.(error);
    }
  }, [url, onOpen, onClose, onMessage, onError, shouldReconnect, reconnectAttempts, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close();
    }
  }, []);

  const sendMessage = useCallback((message) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof message === 'string' ? message : JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  return {
    socket,
    lastMessage,
    readyState,
    connectionStatus,
    sendMessage,
    connect,
    disconnect,
  };
};