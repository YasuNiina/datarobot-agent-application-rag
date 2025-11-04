import { HttpAgent } from '@ag-ui/client';
import type { Message } from '@ag-ui/core';

export function createAgent({
  url,
  threadId,
  initialMessages = [],
  initialState = {},
}: {
  url: string;
  threadId: string;
  initialMessages?: Message[];
  initialState?: any;
}) {
  return new HttpAgent({
    url,
    threadId,
    agentId: threadId,
    initialMessages,
    initialState,
    // headers: { Authorization: 'Bearer token' },
  });
}
