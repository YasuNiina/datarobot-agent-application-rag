import { useEffect, useMemo, useRef, useState } from 'react';
import { v4 as uuid } from 'uuid';
import {
  type RunAgentInput,
  type RunErrorEvent,
  type StateSnapshotEvent,
  type TextMessageContentEvent,
  type TextMessageEndEvent,
  type TextMessageStartEvent,
  type ToolCallEndEvent,
  type CustomEvent,
} from '@ag-ui/core';
import type { AgentSubscriberParams } from '@ag-ui/client';

import { createAgent } from '@/lib/agent';
import {
  createCustomMessageWidget,
  createTextMessageFromAgUiEvent,
  createTextMessageFromUserInput,
  createToolMessageFromAgUiEvent,
} from '@/lib/mappers';
import type { ChatProviderInput } from '@/components/ChatProvider';
import type { MessageResponse } from '@/api/chat/types';
import { useFetchHistory } from '@/api/chat';
import type { Tool, ToolSerialized } from '@/types/tools';
import type { ProgressState } from '@/types/progress';
import { isProgressDone, isProgressError, isProgressStart } from '@/types/events';
import { getApiUrl } from '@/lib/utils';

export type UseAgUiChatParams = ChatProviderInput;

export function useAgUiChat({
  chatId,
  setChatId,
  agUiEndpoint,
  refetchChats = () => Promise.resolve(),
}: UseAgUiChatParams) {
  const [state, setState] = useState<Record<any, any>>({});
  const [messages, setMessages] = useState<MessageResponse[]>([]);
  const [message, setMessage] = useState<MessageResponse | null>(null);
  const [userInput, setUserInput] = useState('');
  const [tools, setTools] = useState<Record<string, Tool<any>>>({});
  const [initialMessages, setInitialMessages] = useState<MessageResponse[]>([]);
  const [initialState, setInitialState] = useState<any>({});
  const [progress, setProgress] = useState<ProgressState>({});
  const [runningAgent, setRunningAgent] = useState(false);
  const toolHandlersRef = useRef<
    Record<string, Pick<Tool<any>, 'handler' | 'render' | 'renderAndWait'>>
  >({});
  if (!chatId) {
    chatId = 'main';
  }

  const {
    data: history,
    isLoading: isLoadingHistory,
    refetch: refetchHistory,
  } = useFetchHistory({ chatId });

  const baseApiUrl = useMemo(getApiUrl, []);
  const agUIUrl = new URL(agUiEndpoint, baseApiUrl).href;

  const agent = useMemo(() => {
    return createAgent({ url: agUIUrl, threadId: chatId });
  }, [chatId]);

  const agentRef = useRef(agent);
  const messageRef = useRef(message);
  const messagesRef = useRef(messages);
  const toolsRef = useRef(tools);
  const unsubscribeRef = useRef<null | Function>(null);

  useEffect(() => {
    agentRef.current = agent;
    messageRef.current = message;
    messagesRef.current = messages;
    toolsRef.current = tools;
  });

  useEffect(() => {
    setMessages([]);
    setMessage(null);
    setProgress({});
    setRunningAgent(false);
    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
      }
      agent.abortController.abort();
    };
  }, [chatId]);

  async function sendMessage(message: string) {
    agent.messages = [{ id: uuid(), role: 'user', content: message }];

    const historyMessage = createTextMessageFromUserInput(message, chatId);
    setMessages(state => [...state, historyMessage]);
    setUserInput('');
    setRunningAgent(true);
    const { unsubscribe } = agent.subscribe({
      onTextMessageStartEvent(params: { event: TextMessageStartEvent } & AgentSubscriberParams) {
        setMessage(createTextMessageFromAgUiEvent(params.event));
      },
      onTextMessageContentEvent(
        params: {
          event: TextMessageContentEvent;
          textMessageBuffer: string;
        } & AgentSubscriberParams
      ) {
        const { event, textMessageBuffer } = params;
        setMessage(createTextMessageFromAgUiEvent(event, textMessageBuffer));
      },
      onTextMessageEndEvent(
        params: { event: TextMessageEndEvent; textMessageBuffer: string } & AgentSubscriberParams
      ) {
        console.debug('onTextMessageEndEvent', params);
        setMessages(state => [...state, messageRef.current!]);
        setMessage(null);
        setRunningAgent(false);
      },
      onToolCallStartEvent(params) {
        console.debug('onToolCallStartEvent', params);
      },
      onToolCallEndEvent(
        params: {
          event: ToolCallEndEvent;
          toolCallName: string;
          toolCallArgs: Record<string, any>;
        } & AgentSubscriberParams
      ) {
        console.debug('onToolCallArgsEvent', params);
        const tool = toolsRef.current[params.toolCallName];
        const toolHandler = toolHandlersRef.current[params.toolCallName];
        if (tool && toolHandler?.handler && params.toolCallArgs) {
          toolHandler.handler(params.toolCallArgs);
          setMessages(state => [
            ...state,
            createToolMessageFromAgUiEvent(params.event, params.toolCallName, params.toolCallArgs),
          ]);
        } else if (tool && toolHandler?.render && params.toolCallArgs) {
          setMessages(state => [
            ...state,
            createCustomMessageWidget({
              toolCallArgs: params.toolCallArgs,
              toolCallName: params.toolCallName,
              threadId: chatId,
            }),
          ]);
        } else {
          setMessages(state => [
            ...state,
            createToolMessageFromAgUiEvent(params.event, params.toolCallName, params.toolCallArgs),
          ]);
        }
      },
      onStateSnapshotEvent(params: { event: StateSnapshotEvent } & AgentSubscriberParams) {
        setState(params.state);
      },
      onStateChanged(params: Omit<AgentSubscriberParams, 'input'> & { input?: RunAgentInput }) {
        setState(params.state);
      },
      onRunFinishedEvent() {
        unsubscribe();
        unsubscribeRef.current = null;
        refetchChats();
      },
      onCustomEvent(params: { event: CustomEvent } & AgentSubscriberParams) {
        const event = params.event;
        console.debug('onCustomEvent', params);

        if (isProgressStart(event)) {
          setProgress(state => ({ ...state, [event.value.id]: event.value.steps }));
        } else if (isProgressDone(event)) {
          setProgress(state => ({
            ...state,
            [event.value.id]: state[event.value.id].map((s, i) =>
              event.value.step === i ? { ...s, done: true } : s
            ),
          }));
        } else if (isProgressError(event)) {
          setProgress(state => ({
            ...state,
            [event.value.id]: state[event.value.id].map((s, i) =>
              event.value.step === i ? { ...s, error: event.value.message } : s
            ),
          }));
        }
      },
      onRunErrorEvent(params: { event: RunErrorEvent } & AgentSubscriberParams) {
        if (params.event.rawEvent?.name === 'AbortError') {
          return;
        }
        setRunningAgent(false);
        setMessages(state => [
          ...state,
          {
            id: uuid(),
            type: 'error',
            role: 'system',
            createdAt: new Date(),
            threadId: chatId,
            error: params.event.message,
          },
        ]);
      },
    });

    unsubscribeRef.current = unsubscribe;

    const result = await agent.runAgent({
      tools: Object.values(tools).filter(tool => tool.enabled !== false),
    });

    console.debug('runAgent result', result);
  }

  const combinedMessages: MessageResponse[] = useMemo(() => {
    const result =
      !isLoadingHistory && !history?.length && initialMessages ? [...initialMessages] : [];
    if (history) {
      result.push(...history);
    }
    result.push(...messages);
    if (message) {
      result.push(message);
    }
    return result;
  }, [history, messages, message, isLoadingHistory]);

  function registerOrUpdateTool(id: string, tool: ToolSerialized) {
    setTools(state => ({
      ...state,
      [id]: tool,
    }));
  }

  function updateToolHandler(
    name: string,
    handler: Pick<Tool<any>, 'handler' | 'render' | 'renderAndWait'>
  ) {
    toolHandlersRef.current[name] = handler;
  }

  function removeTool(name: string) {
    setTools(state => {
      const copy = { ...state };
      delete copy[name];
      return copy;
    });
    delete toolHandlersRef.current[name];
  }

  function getTool(name: string): Tool<any> | null {
    if (tools[name] && toolHandlersRef.current[name]) {
      return {
        ...tools[name],
        ...toolHandlersRef.current[name],
      };
    }

    return null;
  }

  return {
    agent,
    /*state*/
    state,
    setState,
    chatId,
    setChatId,
    messages: combinedMessages,
    setMessages,
    message,
    combinedMessages,
    setMessage,
    userInput,
    setUserInput,
    initialMessages,
    setInitialMessages,
    initialState,
    setInitialState,
    progress,
    setProgress,
    runningAgent,
    setRunningAgent,
    /*methods*/
    sendMessage,
    registerOrUpdateTool,
    updateToolHandler,
    removeTool,
    getTool,
    /*resolver*/
    useFetchHistory,
    isLoadingHistory,
    refetchHistory,
  };
}
