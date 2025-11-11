import { Example } from '@/Example.tsx';
import { ChatProvider } from '@/components/ChatProvider.tsx';
import React, { useState } from 'react';

export const ChatPage: React.FC = () => {
  const agUiEndpoint = 'api/v1/chat';
  const [chatId, setChatId] = useState<string>(() => window.location.hash?.substring(1));

  const setChatIdHandler = (id: string) => {
    setChatId(id);
    window.location.hash = id;
  };

  return (
    <ChatProvider chatId={chatId} setChatId={setChatIdHandler} agUiEndpoint={agUiEndpoint}>
      <Example />
    </ChatProvider>
  );
};
