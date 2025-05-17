import React, { useEffect, useRef } from 'react';
import Message from './Message';
import { useChat } from '../../contexts/ChatContext';

const MessageList: React.FC = () => {
  const { messages } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-850">
      {messages.length === 0 ? (
        <div className="flex items-center justify-center h-full text-gray-500">
          <div className="text-center">
            <p>Upload an image and start a conversation</p>
            <p className="text-sm mt-2">Ask questions like "What's in this image?" or "When was this taken?"</p>
          </div>
        </div>
      ) : (
        messages.map((message, index) => (
          <Message key={index} message={message} />
        ))
      )}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;