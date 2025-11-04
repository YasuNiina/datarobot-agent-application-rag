import { useState } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { SidebarProvider } from '@/components/ui/sidebar';

import { queryClient } from '@/lib/query-client';
import { ChatProvider } from '@/components/ChatProvider';
import { Example } from '@/Example';

// Update to endpoint in your project
const agUiEndpoint = import.meta.env.DEV ? 'api/api/v1/writer-agent' : 'api/v1/writer-agent';

export function App() {
  // TODO: this should be implemented with app specific router integration
  const [chatId, setChatId] = useState<string>(() => window.location.hash?.substring(1));

  const setChatIdHandler = (id: string) => {
    setChatId(id);
    window.location.hash = id;
  };

  return (
    <QueryClientProvider client={queryClient}>
      <SidebarProvider>
        <ChatProvider chatId={chatId} setChatId={setChatIdHandler} agUiEndpoint={agUiEndpoint}>
          <Example />
        </ChatProvider>
      </SidebarProvider>
    </QueryClientProvider>
  );
}
