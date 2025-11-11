import { type PropsWithChildren, useEffect } from 'react';
import { ChatMessages } from '@/components/ChatMessages';
import { ChatTextInput } from '@/components/ChatTextInput';
import type { MessageResponse } from '@/api/chat/types';
import { ChatProgress } from '@/components/ChatProgress';
import { useChatContext } from '@/hooks/use-chat-context';

export type ChatProps = {
  initialMessages?: MessageResponse[];
} & PropsWithChildren;

export function Chat({ initialMessages, children }: ChatProps) {
  const {
    sendMessage,
    userInput,
    setUserInput,
    combinedMessages,
    progress,
    setProgress,
    isLoadingHistory,
    setInitialMessages,
  } = useChatContext();
  useEffect(() => {
    if (initialMessages) {
      setInitialMessages(initialMessages);
    }
  }, []);

  return (
    <div className="main-section">
      {children || (
        <>
          <ChatMessages isLoading={isLoadingHistory} messages={combinedMessages} />
          <ChatProgress progress={progress || {}} setProgress={setProgress} />
          <ChatTextInput userInput={userInput} setUserInput={setUserInput} onSubmit={sendMessage} />
        </>
      )}
    </div>
  );
}
