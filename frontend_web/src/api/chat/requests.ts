import type { MastraMessageV2 } from '@mastra/core';
import type { Message } from '@ag-ui/core';
import { APIChat, APIChatWithMessages, ChatsPage, ErrorMessage, MessagePage } from './types';
import apiClient from '../apiClient';

export function isErrorMessage(m: any): m is ErrorMessage {
  return m.type === 'error';
}

export async function getChats({ signal }: { signal: AbortSignal }): Promise<ChatsPage> {
  const response = await apiClient.get<APIChat[]>('v1/chat', { signal });

  console.log('GET CHAT', response);

  return {
    threads: response.data.map(chat => ({
      id: chat.threadId,
      title: chat.name,
      resourceId: chat.threadId,
      createdAt: chat.createdAt ? new Date(chat.createdAt) : null,
      updatedAt: chat.updateTime ? new Date(chat.updateTime) : null,
    })),
  };
}

export async function deleteChat({ chatId }: any): Promise<void> {
  await apiClient.delete(`v1/chat/${chatId}`);
}

export async function getChatHistory({
  signal,
  chatId,
}: {
  signal: AbortSignal;
  chatId: string;
}): Promise<MessagePage> {
  const response = await apiClient.get<APIChatWithMessages>(`v1/chat/${chatId}`);
  const mastraMessages = [];
  for (const aguiMessage of response.data.messages) {
    const mastraMessage: MastraMessageV2 = {
      id: aguiMessage.id,
      role:
        aguiMessage.role == 'developer' || aguiMessage.role == 'tool' ? 'system' : aguiMessage.role,
      createdAt: aguiMessage?.timestamp ? new Date(aguiMessage.timestamp) : new Date(1678886400000),
      content: {
        format: 2,
        parts: [{ type: 'text', text: aguiMessage.content || '' }],
        content: aguiMessage.content,
      },
    };
    mastraMessages.push(mastraMessage);
  }
  return { messages: mastraMessages };
}
