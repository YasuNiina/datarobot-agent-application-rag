import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar';
import { Skeleton } from '@/components/ui/skeleton';
import {
  MessageSquare,
  MessageSquareText,
  MoreHorizontal,
  Plus,
  Settings,
  LoaderCircle,
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import type { ChatListItem } from '@/api/chat/types';
import { useNavigate } from 'react-router-dom';
import { JSX, useState } from 'react';

export interface ChatSidebarProps {
  isLoading: boolean;
  chatId: string;
  onChatCreate: () => any;
  onChatSelect: (threadId: string) => any;
  onChatDelete: (threadId: string, callbackFn: () => void) => any;
  chats?: ChatListItem[];
}

export function ChatSidebar({
  isLoading,
  chats,
  chatId,
  onChatSelect,
  onChatCreate,
  onChatDelete,
}: ChatSidebarProps) {
  const navigate = useNavigate();
  const goToSettings = () => navigate('/settings');
  const [chatToDelete, setChatToDelete] = useState<string | null>(null);
  const getIcon = (id: string): JSX.Element => {
    if (id === chatToDelete) {
      return <LoaderCircle className="animate-spin" />;
    }
    if (id === chatId) {
      return <MessageSquareText />;
    }
    return <MessageSquare />;
  };

  return (
    <Sidebar className="sidebar">
      <SidebarContent>
        <SidebarGroup>
          <SidebarMenuItem key="open-settings">
            <SidebarMenuButton disabled={isLoading} asChild onClick={goToSettings}>
              <div>
                <Settings />
                <span>Settings</span>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarGroupLabel>Chats</SidebarGroupLabel>
          <SidebarMenuItem key="new-chat">
            <SidebarMenuButton disabled={isLoading} asChild onClick={onChatCreate}>
              <div>
                <Plus />
                <span>Start new chat</span>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarGroupContent>
            <SidebarMenu>
              {isLoading ? (
                <>
                  <Skeleton className="h-8" />
                  <Skeleton className="h-8" />
                  <Skeleton className="h-8" />
                  <Skeleton className="h-8" />
                </>
              ) : (
                !!chats &&
                chats.map((chat: ChatListItem) => (
                  <SidebarMenuItem key={chat.id}>
                    <SidebarMenuButton
                      asChild
                      isActive={chat.id === chatId}
                      onClick={() => onChatSelect(chat.id)}
                    >
                      <div>
                        {getIcon(chat.id)}
                        <span>{chat.name || 'New Chat'}</span>
                      </div>
                    </SidebarMenuButton>
                    {chat.initialised && !chatToDelete && (
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <SidebarMenuAction>
                            <MoreHorizontal />
                          </SidebarMenuAction>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent side="right" align="start">
                          <DropdownMenuItem
                            onClick={() => {
                              setChatToDelete(chat.id);
                              onChatDelete(chat.id, () => setChatToDelete(null));
                            }}
                          >
                            <span>Delete chat</span>
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    )}
                  </SidebarMenuItem>
                ))
              )}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
