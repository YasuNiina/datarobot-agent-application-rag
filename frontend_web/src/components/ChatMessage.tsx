import { User, Bot, Cog, Hammer } from 'lucide-react';
import { cn } from '@/lib/utils';
import type {
  ContentPart,
  MessageContent,
  TextUIPart,
  ToolInvocationUIPart,
} from '@/types/message';
import { memo, useMemo } from 'react';
import { useChatContext } from '@/hooks/use-chat-context';

interface ChatMessageProps {
  id: string;
  role: 'user' | 'assistant' | 'system';
  createdAt: string | Date;
  threadId?: string;
  resourceId?: string;
  content: MessageContent;
  // TODO?
  // content: MessageContent | string;
}

export function UniversalContentPart({ part }: { part: ContentPart }) {
  if (part.type === 'text') {
    return <TextContentPart part={part} />;
  }
  if (part.type === 'tool-invocation') {
    return <ToolInvocationPart part={part} />;
  }
  return null;
}

export function TextContentPart({ part }: { part: TextUIPart }) {
  return <div>{part.text}</div>;
}

export function ToolInvocationPart({ part }: { part: ToolInvocationUIPart }) {
  const { toolInvocation } = part;
  const { toolName } = toolInvocation;
  const ctx = useChatContext();
  const tool = ctx.getTool(toolName);
  if (tool?.render) {
    return tool.render({ status: 'complete', args: toolInvocation.args });
  }
  if (tool?.renderAndWait) {
    return tool.renderAndWait({
      status: 'complete',
      args: toolInvocation.args,
      callback: event => {
        console.log(event);
      },
    });
  }
  return (
    <div>
      <div>Tool: {toolInvocation.toolName}</div>
      {toolInvocation.args?.properties &&
        Object.entries(toolInvocation.args.properties).map(([k, v]) => (
          <div key={k}>
            <strong>{k}:</strong> {v as string}
          </div>
        ))}
      {toolInvocation.args?.type && <span>Type: {toolInvocation.args?.type}</span>}
    </div>
  );
}

export function ChatMessage({
  id,
  role,
  createdAt,
  threadId,
  resourceId,
  content,
}: ChatMessageProps) {
  let Icon = useMemo(() => {
    if (role === 'user') {
      return User;
    } else if (role === 'system') {
      return Cog;
    } else if (content.parts.some(({ type }) => type === 'tool-invocation')) {
      return Hammer;
    } else {
      return Bot;
    }
  }, [role, content.parts]);

  // Convert createdAt to Date if it's a string
  const date = typeof createdAt === 'string' ? new Date(createdAt) : createdAt;

  return (
    <div
      className={cn('flex gap-3 p-4 rounded-lg', role === 'user' ? 'bg-muted/50' : 'bg-card')}
      data-message-id={id}
      data-thread-id={threadId}
      data-resource-id={resourceId}
    >
      <div className="flex-shrink-0">
        <div
          className={cn(
            'w-8 h-8 rounded-full flex items-center justify-center',
            role === 'user'
              ? 'bg-primary text-primary-foreground'
              : role === 'assistant'
                ? 'bg-secondary text-secondary-foreground'
                : 'bg-accent text-accent-foreground'
          )}
        >
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-medium capitalize">{role}</span>
          <span className="text-xs text-muted-foreground">{date.toLocaleTimeString()}</span>
        </div>
        <div className="text-sm whitespace-pre-wrap break-words">
          {content.parts.map((part, i) => (
            <UniversalContentPart key={i} part={part} />
          ))}
        </div>
      </div>
    </div>
  );
}

export const ChatMessagesMemo = memo(ChatMessage);
