import { Send } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Kbd, KbdGroup } from '@/components/ui/kbd';
import { Textarea } from '@/components/ui/textarea';
import type { Dispatch, KeyboardEvent, SetStateAction } from 'react';

export interface ChatTextInputProps {
  onSubmit: (text: string) => any;
  userInput: string;
  setUserInput: Dispatch<SetStateAction<string>>;
  runningAgent: boolean;
}

export function ChatTextInput({
  onSubmit,
  userInput,
  setUserInput,
  runningAgent,
}: ChatTextInputProps) {
  function keyDownHandler(e: KeyboardEvent) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      onSubmit(userInput);
    }
  }

  return (
    <div className="chat-text-input relative">
      <Textarea
        value={userInput}
        onChange={e => setUserInput(e.target.value)}
        onKeyDown={keyDownHandler}
        className="pr-12 text-area"
      ></Textarea>
      <Button
        type="submit"
        onClick={() => onSubmit(userInput)}
        className="absolute bottom-2 right-2"
        size="icon"
        disabled={runningAgent}
      >
        <Send />
      </Button>

      <div className="absolute bottom-2 right-14 text-muted-foreground text-xs select-none">
        <KbdGroup>
          <Kbd>Ctrl + ⏎</Kbd>
          or
          <Kbd>⌘ + ⏎</Kbd>
        </KbdGroup>
      </div>
    </div>
  );
}
