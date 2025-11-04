import { useChatContext } from '@/hooks/use-chat-context';
import { useEffect, useMemo } from 'react';
import z from 'zod/v4';
import type { Tool } from '@/types/tools';

export function useAgUiTool<Shape extends Record<any, any>>(toolWithHandler: Tool<Shape>) {
  const { handler, renderAndWait, render, ...rest } = toolWithHandler;
  const parameters = useMemo(() => {
    const json = z.toJSONSchema(rest.parameters);
    delete json.$schema;
    delete json.additionalProperties;

    return json;
  }, []);
  const name = `ui-${rest.name}`;
  const tool = { ...rest, name, parameters };
  const context = useChatContext();

  useEffect(() => {
    context.registerOrUpdateTool(name, tool);
    context.updateToolHandler(name, { handler, renderAndWait, render });

    return () => {
      context.removeTool(name);
    };
  }, [tool.name, tool.description]);

  useEffect(() => {
    context.updateToolHandler(name, { handler, renderAndWait, render });
  }, [handler, renderAndWait, render, name]);
}
