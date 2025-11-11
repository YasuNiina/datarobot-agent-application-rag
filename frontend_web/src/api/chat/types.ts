import type { MastraMessageV2 } from '@mastra/core';
import type { Message } from '@ag-ui/core';

// TODO: This awkwardly shoves AGUI message list into the Mastra format.
// I didn't want to completely rewrite the UI, still figuring out where to go here.

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

export type MessageResponse = MastraMessageV2 | ErrorMessage;

export type MessagePage = {
  messages: MessageResponse[];
};
export type ChatsPage = {
  threads: ChatResponse[];
};

export type APIChat = {
  name: string;
  threadId?: string;
  createdAt: Date;
  updateTime: Date;
};

export type APIChatWithMessages = APIChat & {
  messages: Message[];
};
