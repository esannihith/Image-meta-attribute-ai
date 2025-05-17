import React, { useState, useRef } from 'react';
import { UploadIcon, XIcon } from 'lucide-react';
import { useChat } from '../../contexts/ChatContext';
import Button from '../common/Button';
import ImagePreview from './ImagePreview';

const ImageUploader: React.FC = () => {
  const { uploadImage, imageUrl, clearImage, isProcessing, uploadProgress } = useChat();
  // ref to the hidden file input
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [dragActive, setDragActive] = useState(false);
  
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };
  
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };
  
  const handleFile = (file: File) => {
    // Check if file is an image
    if (!file.type.match('image.*')) {
      alert('Please upload an image file (JPEG, PNG)');
      return;
    }
    
    // Check file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert('File is too large. Maximum size is 5MB.');
      return;
    }
    
    uploadImage(file);
  };

  return (
    <div className="flex flex-col bg-gray-800 rounded-lg overflow-hidden border border-gray-700 shadow-lg h-[600px] max-h-[calc(100vh-12rem)]">
      {!imageUrl ? (
        <div
          className={`
            flex flex-col items-center justify-center h-full p-6
            border-2 border-dashed rounded-md transition-colors
            ${dragActive 
              ? 'border-blue-500 bg-blue-500/10' 
              : 'border-gray-600 hover:border-gray-500'}
          `}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <UploadIcon 
            className="h-16 w-16 text-gray-500 mb-4" 
            strokeWidth={1.5} 
          />
          <p className="text-lg text-center mb-2">
            Drag and drop your image here
          </p>
          <p className="text-sm text-gray-500 text-center mb-6">
            Supports JPEG, PNG (Max 5MB)
          </p>
          <label className="cursor-pointer">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg, image/png"
              onChange={handleChange}
              className="hidden"
            />
            <Button
              type="button"
              onClick={(e) => {
                e.preventDefault();
                fileInputRef.current?.click();
              }}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md transition-colors"
            >
              Select Image
            </Button>
          </label>
        </div>
      ) : (
        <div className="flex flex-col h-full">
          <div className="p-4 border-b border-gray-700 flex items-center justify-between">
            <h2 className="font-medium text-lg">Image Preview</h2>
            <button
              onClick={clearImage}
              className="text-gray-400 hover:text-white p-1 rounded-full hover:bg-gray-700 transition-colors"
              aria-label="Remove image"
            >
              <XIcon size={18} />
            </button>
          </div>
          {isProcessing && uploadProgress < 100 && (
            <div className="px-4 py-2 bg-gray-750 border-b border-gray-700">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-gray-300">Uploading image...</span>
                <span className="text-sm text-gray-400">{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-600 rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300 ease-in-out" 
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
            </div>
          )}
          <div className="flex-1 overflow-y-auto p-4">
            <ImagePreview imageUrl={imageUrl} />
          </div>
        </div>
      )}
    </div>
  );
};

export default ImageUploader;