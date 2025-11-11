import { useInfiniteQuery, useMutation, useQuery } from '@tanstack/react-query';
import { deleteChat, getChatHistory, getChats, type PaginationInfo } from '@/api/chat/requests';
import { chatsKeys } from '@/api/chat/keys';
import { selectChats, selectMessages } from '@/api/chat/selectors';

const staleTime = 60 * 1000;

export function useFetchChats() {
  return useQuery({
    queryFn: ({ signal }) => getChats({ signal }),
    queryKey: chatsKeys.list,
    select: selectChats,
    staleTime,
  });
}
export function useDeleteChat() {
  return useMutation({
    mutationFn: ({ chatId }: { chatId: string }) => deleteChat({ chatId }),
  });
}

export function useFetchHistory({ chatId }: { chatId: string }) {
  return useInfiniteQuery({
    initialPageParam: 0,
    queryKey: chatsKeys.history(chatId!),
    queryFn: ({ signal, pageParam = 0 }) => getChatHistory({ signal, chatId, offset: pageParam }),
    getNextPageParam: lastPage => getOffestFromPage(lastPage),
    enabled: !!chatId,
    select: selectMessages,
    staleTime,
  });
}

function getOffestFromPage(page: PaginationInfo) {
  if (page.hasMore) {
    return page.page + 1;
  }
}
