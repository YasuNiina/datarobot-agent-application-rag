import { Chat } from '@/components/Chat';
import { v4 as uuid } from 'uuid';
import z from 'zod/v4';
import { isErrorMessage, type MessageResponse } from '@/api-state/chats/api-requests';
import { useChatContext } from '@/hooks/use-chat-context';
// import { ChatSidebar } from '@/components/ChatSidebar';
import { useAgUiTool } from '@/hooks/use-ag-ui-tool';
import { ChatMessages } from '@/components/ChatMessages';
import { ChatProgress } from '@/components/ChatProgress';
import { ChatTextInput } from '@/components/ChatTextInput';
import { ChatError } from '@/components/ChatError';
import { ChatMessagesMemo } from '@/components/ChatMessage';

const initialMessages: MessageResponse[] = [
  {
    id: uuid(),
    role: 'assistant',
    content: {
      format: 2,
      parts: [
        {
          type: 'text',
          text: `Hi. I offer features that allow you to plan activities based on the weather, display customizable weather widgets, and show on-page alerts.`,
        },
      ],
    },
    createdAt: new Date(),
  },
];

export function Example() {
  const {
    // chatId,
    // setChatId,
    sendMessage,
    userInput,
    setUserInput,
    combinedMessages,
    progress,
    setProgress,
    isLoadingHistory,
  } = useChatContext();

  useAgUiTool({
    name: 'alert',
    description: 'Action. Display an alert to user',
    handler: ({ message }) => alert(message),
    parameters: z.object({
      message: z.string().describe('The message which will be displayed to user'),
    }),
  });

  return (
    <div className="chat">
      {/*<ChatSidebar chatId={chatId} setChatId={setChatId} />*/}

      <Chat initialMessages={initialMessages}>
        <ChatMessages isLoading={isLoadingHistory} messages={combinedMessages}>
          {combinedMessages &&
            combinedMessages.map(m => {
              if (isErrorMessage(m)) {
                return <ChatError key={m.id} message={m.error} createdAt={m.createdAt} />;
              }
              return <ChatMessagesMemo key={m.id} {...(m as any)} />;
            })}
        </ChatMessages>
        <ChatProgress progress={progress || {}} setProgress={setProgress} />
        <ChatTextInput userInput={userInput} setUserInput={setUserInput} onSubmit={sendMessage} />
      </Chat>
    </div>
  );
}
