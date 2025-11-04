import { createContext } from 'react';
import { useAgUiChat } from '@/hooks/use-ag-ui-chat';
import { HttpAgent } from '@ag-ui/client';

export type AgUiChatReturn = ReturnType<typeof useAgUiChat>;

export const ChatContext = createContext<AgUiChatReturn>({
  agent: new HttpAgent({ url: '' }),
  /*state*/
  state: {},
  setState: () => {},
  chatId: '',
  setChatId: () => {},
  messages: [],
  setMessages: () => {},
  message: null,
  combinedMessages: [],
  setMessage: () => {},
  userInput: '',
  setUserInput: () => {},
  initialMessages: [],
  setInitialMessages: () => {},
  initialState: {},
  setInitialState: () => {},
  progress: {},
  setProgress: () => {},
  /*methods*/
  sendMessage: () => Promise.resolve(),
  registerOrUpdateTool: () => {},
  updateToolHandler: () => {},
  removeTool: () => {},
  getTool: () => null,
  /*resolver*/
  useFetchHistory: () => ({}) as any,
  isLoadingHistory: false,
  refetchHistory: () => Promise.resolve({} as any),
} as AgUiChatReturn);
