import React, { useState } from 'react';
import { SendIcon } from 'lucide-react';
import { useChat } from '../../contexts/ChatContext';
import Button from '../common/Button';

const MessageInput: React.FC = () => {
  const [input, setInput] = useState('');
  const { sendMessage, imageUrl, isProcessing, uploadProgress } = useChat();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isProcessing) {
      sendMessage(input);
      setInput('');
    }
  };

  return (
    <form 
      onSubmit={handleSubmit}
      className="border-t border-gray-700 p-3 bg-gray-800"
    >
      <div className="flex items-center">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            !imageUrl 
              ? "Upload an image first..." 
              : isProcessing
                ? (uploadProgress < 100
                    ? `Uploading image (${uploadProgress}%)...`
                    : "Analyzing image...")
                : "Ask about the image..."
          }
          disabled={!imageUrl || isProcessing}
          className="flex-1 bg-gray-700 border border-gray-600 rounded-l-md py-2 px-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        />
        <Button 
          type="submit"
          disabled={!input.trim() || !imageUrl || isProcessing}
          className="bg-blue-600 hover:bg-blue-700 text-white rounded-r-md py-2 px-4 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <SendIcon size={18} />
        </Button>
      </div>
    </form>
  );
};

export default MessageInput;