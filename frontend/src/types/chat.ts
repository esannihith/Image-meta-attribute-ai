export interface MessageType {
  content: string;
  sender: 'user' | 'ai';
  timestamp: string;
}