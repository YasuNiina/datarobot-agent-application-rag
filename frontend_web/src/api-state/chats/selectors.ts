import type { InfiniteData } from '@tanstack/react-query';
import type { ChatsPage, MessagePage } from '@/api-state/chats/api-requests';

export function selectChats(res: ChatsPage) {
  return res.threads;
}
export function selectMessages(res: InfiniteData<MessagePage, number>) {
  return res.pages.flatMap(page => page.messages);
}
