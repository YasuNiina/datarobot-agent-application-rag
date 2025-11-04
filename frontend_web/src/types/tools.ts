import type { ZodType } from 'zod/v4';
import type { ReactElement } from 'react';

export const ToolStatus = {
  EXECUTING: 'executing',
  COMPLETE: 'complete',
} as const;

export interface ToolState<Shape extends Record<any, any>> {
  status: (typeof ToolStatus)[keyof typeof ToolStatus];
  args: Shape;
  callback?: (response: any) => any;
}

export interface Tool<Shape extends Record<any, any>> {
  /**
   * Unique name
   */
  name: string;
  /**
   * Describe the instrument, this will be passed to LLM
   */
  description: string;
  /**
   * Define a z.object(), import zod from 'zod/v4
   */
  parameters: ZodType<Shape>;
  /**
   * Handler for a UI action
   */
  handler?: (args: Shape) => void | Promise<void>;
  /**
   * Render custom UI component
   */
  render?: (state: ToolState<Shape>) => ReactElement;
  renderAndWait?: (state: ToolState<Shape>) => ReactElement;
  enabled?: boolean;
}

export interface ToolSerialized {
  name: string;
  description: string;
  parameters: any;
  enabled?: boolean;
}
