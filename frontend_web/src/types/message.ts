// These types are copied from @ai-sdk
// TODO most likely will be replaced after history shape is defined
export type ContentPart =
  | TextUIPart
  | ReasoningUIPart
  | ToolInvocationUIPart
  | SourceUIPart
  | FileUIPart
  | StepStartUIPart;

export type MessageContent = {
  format: number;
  parts: ContentPart[];
  content: string;
};

/**
 * A text part of a message.
 */
export type TextUIPart = {
  type: 'text';
  /**
   * The text content.
   */
  text: string;
};
/**
 * A reasoning part of a message.
 */
export type ReasoningUIPart = {
  type: 'reasoning';
  /**
   * The reasoning text.
   */
  reasoning: string;
  details: Array<
    | {
        type: 'text';
        text: string;
        signature?: string;
      }
    | {
        type: 'redacted';
        data: string;
      }
  >;
};
/**
 * A tool invocation part of a message.
 */
export type ToolInvocationUIPart = {
  type: 'tool-invocation';
  /**
   * The tool invocation.
   */
  toolInvocation: any;
};
/**
 * A source part of a message.
 */
export type SourceUIPart = {
  type: 'source';
  /**
   * The source.
   */
  // TODO?
  source: any;
};
/**
 * A file part of a message.
 */
export type FileUIPart = {
  type: 'file';
  mimeType: string;
  data: string;
};
/**
 * A step boundary part of a message.
 */
export type StepStartUIPart = {
  type: 'step-start';
};
