import React from 'react';
import ChatContainer from '../Chat/ChatContainer';
import ImageUploader from '../ImageUpload/ImageUploader';
import { useChat } from '../../contexts/ChatContext';

const Main: React.FC = () => {
  const { imageUrl } = useChat();

  return (
    <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full">
        <div className="flex flex-col">
          <ImageUploader />
        </div>
        <div className="flex flex-col bg-gray-800 rounded-lg overflow-hidden border border-gray-700 shadow-lg">
          <ChatContainer />
        </div>
      </div>
    </main>
  );
};

export default Main;