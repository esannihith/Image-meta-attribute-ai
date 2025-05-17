import React from 'react';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import { useChat } from '../../contexts/ChatContext';

const ChatContainer: React.FC = () => {
  const { imageUrl, isProcessing, uploadProgress } = useChat();
  
  return (
    <div className="flex flex-col h-[600px] max-h-[calc(100vh-12rem)]">
      <div className="p-4 border-b border-gray-700 bg-gray-800">
        <h2 className="font-medium text-lg">Chat with AI about your image</h2>
        {isProcessing && (
          <div className="text-sm text-blue-400 animate-pulse mt-1">
            {uploadProgress < 100 
              ? `Uploading image... (${uploadProgress}%)`
              : 'Analyzing image...'
            }
          </div>
        )}
      </div>
      <MessageList />
      <MessageInput />
    </div>
  );
};

export default ChatContainer;