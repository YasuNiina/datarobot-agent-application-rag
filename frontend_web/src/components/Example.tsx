import { Chat } from '@/components/Chat';
// import type { Message } from '@ag-ui/core';
// import { v4 as uuid } from 'uuid';
// import z from 'zod/v4';
// import { useAgUiTool } from '@/hooks/use-ag-ui-tool';
// import { WeatherWidget } from '@/components/WeatherWidget';
import type { MessageResponse } from '@/api-state/chats/api-requests';

const initialMessages: MessageResponse[] = [
  // {
  //   id: uuid(),
  //   role: 'assistant',
  //   content: {
  //     format: 2,
  //     parts: [
  //       {
  //         type: 'text',
  //         text: `Hi. I can help you
  //   - plan activities taking into account the weather (example for flow);
  //   - show weather in a custom widget;
  //   - show alert on the page;
  //   `,
  //       },
  //     ],
  //   },
  //   createdAt: new Date(),
  // },
];

export function Example() {
  // useAgUiTool({
  //   name: 'alert',
  //   description: 'Action. Display an alert to user',
  //   handler: ({ message }) => alert(message),
  //   parameters: z.object({
  //     message: z.string().describe('The message which will be displayed to user'),
  //   }),
  // });
  // useAgUiTool({
  //   name: 'weather',
  //   description: 'Widget. Displays weather result to user',
  //   render: ({ args }) => {
  //     return <WeatherWidget {...args} />;
  //   },
  //   parameters: z.object({
  //     temperature: z.number(),
  //     feelsLike: z.number(),
  //     humidity: z.number(),
  //     windSpeed: z.number(),
  //     windGust: z.number(),
  //     conditions: z.string(),
  //     location: z.string(),
  //   }),
  // });

  return <Chat initialMessages={initialMessages} />;
}
