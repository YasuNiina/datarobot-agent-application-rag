import { type PropsWithChildren } from 'react';
import { useAgUiChat } from '@/hooks/use-ag-ui-chat';
import { ChatContext } from './context';
import { useFetchChats } from '@/api-state/chats';

export type ChatProviderInput = {
  agUiEndpoint: string;
  chatId: string;
  setChatId: (id: string) => void;
  refetchChats?: () => Promise<any>;
};
export type ChatProviderProps = ChatProviderInput & PropsWithChildren;

export function ChatProvider({ children, agUiEndpoint, chatId, setChatId }: ChatProviderProps) {
  const { refetch } = useFetchChats();
  const refetchChats = refetch || (() => Promise.resolve());
  const value = useAgUiChat({
    agUiEndpoint,
    chatId,
    setChatId,
    refetchChats,
  });
  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}
