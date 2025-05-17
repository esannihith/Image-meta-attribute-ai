import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';

interface SocketContextType {
  socket: Socket | null;
  isConnected: boolean;
  sendToSocket: (event: string, data: any) => void;
}

const SocketContext = createContext<SocketContextType>({
  socket: null,
  isConnected: false,
  sendToSocket: () => {},
});

export const useSocket = () => useContext(SocketContext);

interface SocketProviderProps {
  children: React.ReactNode;
}

export const SocketProvider: React.FC<SocketProviderProps> = ({ children }) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Backend URL (fallback to localhost)
    const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';
    // Initialize Socket.IO client with matching path and transports
    const socketInstance = io(backendUrl, {
      transports: ['websocket'],
      path: '/socket.io',
      autoConnect: true,
    });

    socketInstance.on('connect', () => {
      console.log('Socket connected');
      setIsConnected(true);
    });

    socketInstance.on('disconnect', () => {
      console.log('Socket disconnected');
      setIsConnected(false);
    });

    socketInstance.on('connect_error', (err) => {
      console.error('Connection error:', err);
      setIsConnected(false);
    });

    setSocket(socketInstance);

    return () => {
      socketInstance.disconnect();
    };
  }, []);

  const sendToSocket = useCallback(
    (event: string, data: any) => {
      socket?.emit(event, data);
    },
    [socket]
  );

  return (
    <SocketContext.Provider value={{ socket, isConnected, sendToSocket }}>
      {children}
    </SocketContext.Provider>
  );
};