import { useEffect, useMemo, useRef, useState } from 'react';
import { v4 as uuid } from 'uuid';
import type { ChatResponse } from '@/api/chat/types';
import { useDeleteChat, useFetchChats } from '@/api/chat';

export type UseChatListParams = { chatId: string; setChatId: (id: string) => void };

export function useChatList({ chatId, setChatId }: UseChatListParams) {
  const [newChat, setNewChat] = useState<ChatResponse | null>(null);
  const newChatRef = useRef<ChatResponse | null>(null);

  const { mutateAsync: deleteChatMutation } = useDeleteChat();
  const { data: chats, isLoading: isLoadingChats, refetch } = useFetchChats();

  useEffect(() => {
    if (chats?.some(chat => chat.id === newChat?.id)) {
      setNewChat(null);
    }
  }, [chats]);

  useEffect(() => {
    newChatRef.current = newChat;
  });

  const chatsWithNew = useMemo(() => {
    if (chats?.some(chat => chat.id === newChat?.id)) {
      return chats;
    }
    return newChat ? [newChat, ...(chats || [])] : chats;
  }, [chats, newChat]);

  const refetchChats = (): Promise<any> => {
    return newChatRef.current ? refetch() : Promise.resolve();
  };

  /**
   * Returns new chat id
   */
  const createChat = (name: string): string => {
    const newChatID = uuid();
    setNewChat({
      id: newChatID,
      title: name,
      resourceId: '',
      createdAt: new Date(),
      updatedAt: new Date(),
    });
    return newChatID;
  };

  const deleteChat = (chatId: string) => {
    return deleteChatMutation({ chatId }).then(refetch);
  };

  useEffect(() => {
    if (isLoadingChats || !chats || chats?.find(c => c.id === chatId)) {
      return;
    }
    if (!chats.length) {
      addChatHandler();
    } else {
      setChatId(chats[0].id);
    }
  }, [chats, isLoadingChats]);

  function addChatHandler() {
    const newChatID = createChat('New');
    setChatId(newChatID);
  }

  function deleteChatHandler(id: string) {
    deleteChat(id).then(() => {
      refetchChats();
    });
  }

  return {
    chatId,
    setChatId,
    chats,
    chatsWithNew,
    newChat,
    setNewChat,
    createChat,
    isLoadingChats,
    refetchChats,
    deleteChat,
    addChatHandler,
    deleteChatHandler,
  };
}
