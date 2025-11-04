import { type PropsWithChildren } from 'react';
import { ChatSidebarUi } from '@/components/ChatSidebarUi';
import { useChatList } from '@/hooks/use-chat-list';

export type ChatSidebarProps = {
  chatId: string;
  setChatId: (id: string) => any;
} & PropsWithChildren;
export function ChatSidebar({ chatId, setChatId }: ChatSidebarProps) {
  const { chatsWithNew, isLoadingChats, addChatHandler, deleteChatHandler } = useChatList({
    chatId,
    setChatId,
  });

  return (
    <ChatSidebarUi
      isLoading={isLoadingChats}
      chatId={chatId}
      chats={chatsWithNew}
      onChatCreate={addChatHandler}
      onChatSelect={setChatId}
      onChatDelete={deleteChatHandler}
    />
  );
}
