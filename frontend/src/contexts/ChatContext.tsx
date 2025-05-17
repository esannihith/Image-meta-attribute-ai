import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import { useSocket } from './SocketContext';
import { MessageType } from '../types/chat';

interface ChatContextType {
  messages: MessageType[];
  imageUrl: string;
  isProcessing: boolean;
  uploadProgress: number;
  sendMessage: (content: string) => void;
  uploadImage: (file: File) => void;
  clearImage: () => void;
}

const ChatContext = createContext<ChatContextType>({
  messages: [],
  imageUrl: '',
  isProcessing: false,
  uploadProgress: 0,
  sendMessage: () => {},
  uploadImage: () => {},
  clearImage: () => {},
});

export const useChat = () => useContext(ChatContext);

interface ChatProviderProps {
  children: React.ReactNode;
}

export const ChatProvider: React.FC<ChatProviderProps> = ({ children }) => {
  const [messages, setMessages] = useState<MessageType[]>([]);
  const [imageUrl, setImageUrl] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const { socket, sendToSocket, isConnected } = useSocket();
  const responseTimeoutRef = useRef<number | null>(null);

  // Sync with backend Socket.IO events
  useEffect(() => {
    if (!socket) return;

    // On disconnect, clear lock and timeout
    socket.on('disconnect', () => {
      setIsProcessing(false);
      if (responseTimeoutRef.current) {
        clearTimeout(responseTimeoutRef.current);
        responseTimeoutRef.current = null;
      }
    });

    // Handle messages from server
    socket.on('message', (data: { role: 'system' | 'assistant'; content: string }) => {
      setMessages((prev) => [
        ...prev,
        { content: data.content, sender: 'ai', timestamp: new Date().toISOString() }
      ]);
      setIsProcessing(false);
      if (responseTimeoutRef.current) {
        clearTimeout(responseTimeoutRef.current);
        responseTimeoutRef.current = null;
      }
    });

    // Typing indicator
    socket.on('typing', (data: { status: boolean }) => {
      setIsProcessing(data.status);
    });

    // Metadata results from HTTP upload
    socket.on('metadata_result', (data: { metadata: any; analysis?: string; original_prompt?: string }) => {
      if (data.analysis) {
        setMessages((prev) => [
          ...prev,
          { content: data.analysis || '', sender: 'ai', timestamp: new Date().toISOString() }
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          { 
            content: 'Image processed successfully! I can now answer questions about it.', 
            sender: 'ai', 
            timestamp: new Date().toISOString() 
          }
        ]);
      }
      setIsProcessing(false);
      setUploadProgress(100);
      if (responseTimeoutRef.current) {
        clearTimeout(responseTimeoutRef.current);
        responseTimeoutRef.current = null;
      }
    });

    // Error events
    socket.on('error', (error: { message: string }) => {
      setMessages((prev) => [
        ...prev,
        { content: `Error: ${error.message}`, sender: 'ai', timestamp: new Date().toISOString() }
      ]);
      setIsProcessing(false);
      if (responseTimeoutRef.current) {
        clearTimeout(responseTimeoutRef.current);
        responseTimeoutRef.current = null;
      }
    });

    return () => {
      socket.off('message');
      socket.off('typing');
      socket.off('metadata_result');
      socket.off('error');
      socket.off('disconnect');
    };
  }, [socket]);

  const addMessage = useCallback((message: MessageType) => {
    setMessages((prev) => [...prev, message]);
  }, []);

  const sendMessage = useCallback(
    (content: string) => {
      // Must have an image to ask about
      if (!imageUrl) return;

      // Add user message to chat
      const userMessage: MessageType = {
        content,
        sender: 'user',
        timestamp: new Date().toISOString(),
      };
      addMessage(userMessage);

      // If socket is disconnected, show error message
      if (!isConnected) {
        addMessage({
          content: 'There is a problem processing your request, please try again later',
          sender: 'ai',
          timestamp: new Date().toISOString(),
        });
        return;
      }

      // Lock input until server responds
      setIsProcessing(true);

      // Start a timeout to reset lock if no response
      if (responseTimeoutRef.current) clearTimeout(responseTimeoutRef.current);
      responseTimeoutRef.current = window.setTimeout(() => {
        setIsProcessing(false);
        addMessage({ content: 'Server timeout. Please try again.', sender: 'ai', timestamp: new Date().toISOString() });
        responseTimeoutRef.current = null;
      }, 60000);

      // Send message to server
      sendToSocket('message', { content, image_path: localStorage.getItem('current_image_path') });
    },
    [addMessage, sendToSocket, isConnected, imageUrl]
  );

  const uploadImage = useCallback(
    async (file: File) => {
      try {
        // Create object URL for preview
        const objectUrl = URL.createObjectURL(file);
        setImageUrl(objectUrl);
        setUploadProgress(0);
        
        // Reset message state
        if (!isConnected) {
          addMessage({
            content: 'Socket connection not established. Image preview is available, but you cannot communicate with the AI.',
            sender: 'ai',
            timestamp: new Date().toISOString(),
          });
          return;
        }
        
        // Create FormData for HTTP POST request
        const formData = new FormData();
        formData.append('file', file); // 'file' is the key expected by the backend
        
        // Add socket ID to help backend route responses back to this client
        if (socket && socket.id) {
          formData.append('socket_id', socket.id);
        }
        
        setIsProcessing(true);
        
        // Get the backend URL from the environment or fallback to localhost
        const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';
        
        // Use fetch with XMLHttpRequest to track upload progress
        const xhr = new XMLHttpRequest();
        
        // Setup progress tracking
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const progress = Math.round((event.loaded / event.total) * 100);
            setUploadProgress(progress);
          }
        });
        
        // Setup completion handler
        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            const response = JSON.parse(xhr.responseText);
            if (response.success && response.metadata) {
              // Removed manual success message here to avoid duplicates
              // Emit event to analyze the image
              sendToSocket('analyze_image', {
                image_path: response.metadata.file_info.file_path,
              });
            }
          } else {
            // Handle HTTP error
            const errorMsg = xhr.responseText 
              ? JSON.parse(xhr.responseText).error || 'Upload failed'
              : 'Upload failed';
              
            addMessage({
              content: `Error uploading image: ${errorMsg}`,
              sender: 'ai',
              timestamp: new Date().toISOString(),
            });
            setIsProcessing(false);
          }
        });
        
        // Setup error handler
        xhr.addEventListener('error', () => {
          addMessage({
            content: 'Error uploading image. Please try again later.',
            sender: 'ai',
            timestamp: new Date().toISOString(),
          });
          setIsProcessing(false);
        });
        
        // Open and send the request
        xhr.open('POST', `${backendUrl}/upload`);
        xhr.send(formData);
      } catch (error) {
        console.error('Error uploading image:', error);
        addMessage({
          content: `Error uploading image: ${error instanceof Error ? error.message : 'Unknown error'}`,
          sender: 'ai',
          timestamp: new Date().toISOString(),
        });
        setIsProcessing(false);
      }
    },
    [isConnected, socket, addMessage, sendToSocket]
  );

  const clearImage = useCallback(() => {
    setImageUrl('');
    // Clear the stored image path
    localStorage.removeItem('current_image_path');
    // Optionally notify the server
    if (isConnected) {
      sendToSocket('clear_image', {});
    }
    // Clear messages as well
    setMessages([]);
  }, [isConnected, sendToSocket]);

  return (
    <ChatContext.Provider
      value={{
        messages,
        imageUrl,
        isProcessing,
        uploadProgress,
        sendMessage,
        uploadImage,
        clearImage,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};