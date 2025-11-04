import type { MastraMessageV2 } from '@mastra/core';

export type PaginationInfo = {
  total: number;
  page: number;
  perPage: number;
  hasMore: boolean;
};

export interface ChatResponse {
  id: string;
  title?: string;
  resourceId: string;
  createdAt: Date;
  updatedAt: Date;
  metadata?: Record<string, unknown>;
}

export type ErrorMessage = {
  id: string;
  role: 'system';
  createdAt: Date;
  threadId?: string;
  resourceId?: string;
  type?: string;
  error: string;
};

export function isErrorMessage(m: any): m is ErrorMessage {
  return m.type === 'error';
}

// TODO figure out what to do with history schema
export type MessageResponse = MastraMessageV2 | ErrorMessage;

export type MessagePage = PaginationInfo & {
  messages: MessageResponse[];
};
export type ChatsPage = PaginationInfo & {
  threads: ChatResponse[];
};

export function getChats({ signal }: { signal: AbortSignal }): Promise<ChatsPage> {
  return fetch('api/v1/chats', { signal }).then(res => res.json());
}

export function deleteChat({ chatId }: any): Promise<any> {
  return fetch(`api/v1/chats/${chatId}`, { method: 'DELETE' });
}

export function getChatHistory({
  signal,
  chatId,
  offset,
}: {
  signal: AbortSignal;
  chatId: string;
  offset: number;
}): Promise<MessagePage> {
  const params = new URLSearchParams([['offset', `${offset}`]]);
  return fetch(`api/v1/chats/${chatId}/history?${params}`, { signal }).then(res => res.json());
}
