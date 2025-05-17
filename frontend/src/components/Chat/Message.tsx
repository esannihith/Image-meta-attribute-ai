import React from 'react';
import { UserIcon, ServerIcon } from 'lucide-react';
import { MessageType } from '../../types/chat';

interface MessageProps {
  message: MessageType;
}

const Message: React.FC<MessageProps> = ({ message }) => {
  const { content, sender, timestamp } = message;
  
  const isUser = sender === 'user';
  
  return (
    <div 
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-fadeIn`}
    >
      <div 
        className={`
          flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'}
        `}
      >
        <div 
          className={`
            flex items-center justify-center h-8 w-8 rounded-full mx-2 flex-shrink-0 
            ${isUser ? 'bg-blue-600' : 'bg-gray-700'}
          `}
        >
          {isUser ? <UserIcon size={16} /> : <ServerIcon size={16} />}
        </div>
        <div>
          <div 
            className={`
              rounded-2xl py-2 px-3 
              ${isUser 
                ? 'bg-blue-600 text-white rounded-tr-none' 
                : 'bg-gray-700 text-gray-100 rounded-tl-none'}
            `}
          >
            {content}
          </div>
          <div 
            className={`
              text-xs mt-1 text-gray-500
              ${isUser ? 'text-right mr-2' : 'ml-2'}
            `}
          >
            {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Message;