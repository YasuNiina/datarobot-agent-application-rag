import { type PropsWithChildren, useEffect, useRef } from 'react';
import { isErrorMessage, type MessageResponse } from '@/api-state/chats/api-requests';
import { Skeleton } from '@/components/ui/skeleton';
import { ChatMessagesMemo } from '@/components/ChatMessage';
import { ChatError } from '@/components/ChatError';

export type ChatMessageProps = {
  isLoading: boolean;
  messages?: MessageResponse[];
} & PropsWithChildren;

export function ChatMessages({ children, messages, isLoading }: ChatMessageProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="messages">
      <div className="messages-scroll" ref={scrollContainerRef}>
        {isLoading ? (
          <div className="p-4 space-y-4">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
          </div>
        ) : (
          children ||
          (messages &&
            messages.map(m => {
              if (isErrorMessage(m)) {
                return <ChatError key={m.id} message={m.error} createdAt={m.createdAt} />;
              }
              return <ChatMessagesMemo key={m.id} {...(m as any)} />;
            }))
        )}
      </div>
    </div>
  );
}
