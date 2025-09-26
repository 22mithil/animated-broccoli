import { useMemo, useState, useCallback } from 'react';
import { AppSidebar } from '@/components/ui/app-sidebar';
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from '@/components/ui/sidebar';
import {
  SignedIn,
  SignedOut,
  SignInButton,
  UserButton,
} from '@clerk/clerk-react';
import Chat from '@/components/chat/chat';

export default function ChatLayout() {
  const [conversations, setConversations] = useState([
    {
      id: 'sample-1',
      title: 'Chat',
      messages: [
        {
          id: 'm1',
          role: 'user',
          content: 'Hey Bolt, can you tell me more about AI Agents?',
        },
        {
          id: 'm2',
          role: 'assistant',
          content:
            'AI agents are software that perceive their environment and act autonomously to achieve goals, making decisions, learning, and interacting. For example, an AI agent might schedule meetings by resolving conflicts, contacting participants, and finding optimal times—all without constant supervision. Let me know if you‘d like more details!',
        },
        { id: 'm3', role: 'user', content: 'All clear, thank you!' },
      ],
    },
  ]);
  const [selectedId, setSelectedId] = useState(conversations[0]?.id || null);
  const [isNewChat, setIsNewChat] = useState(false);

  const selectedConversation = useMemo(
    () => conversations.find((c) => c.id === selectedId) || null,
    [conversations, selectedId]
  );

  const handleNewChat = useCallback(() => {
    const id = `chat-${Date.now()}`;
    const newConv = { id, title: 'New chat', messages: [] };
    setConversations((prev) => [newConv, ...prev]);
    setSelectedId(id);
    setIsNewChat(true);
  }, []);

  const handleSelect = useCallback(
    (item) => {
      if (item?.id) {
        setSelectedId(item.id);
        setIsNewChat(
          (conversations.find((c) => c.id === item.id)?.messages?.length ||
            0) === 0
        );
      }
    },
    [conversations]
  );

  const handleRename = useCallback((item) => {
    const name = window.prompt('Rename conversation', item.title || 'Untitled');
    if (!name) return;
    setConversations((prev) =>
      prev.map((c) => (c.id === item.id ? { ...c, title: name } : c))
    );
  }, []);

  const handleDelete = useCallback((item) => {
    setConversations((prev) => prev.filter((c) => c.id !== item.id));
    setSelectedId((prev) => (prev === item.id ? null : prev));
    setIsNewChat(false);
  }, []);

  const handleSend = useCallback(
    (text) => {
      setConversations((prev) => {
        const idx = prev.findIndex((c) => c.id === selectedId);
        if (idx === -1) return prev;
        const conv = prev[idx];
        const userMessage = {
          id: `m-${Date.now()}`,
          role: 'user',
          content: text,
        };
        const assistantMessage = {
          id: `m-${Date.now()}-a`,
          role: 'assistant',
          content: 'Thanks! This is a placeholder response.',
        };
        const updated = {
          ...conv,
          messages: [...conv.messages, userMessage, assistantMessage],
        };
        const next = [...prev];
        next[idx] = updated;
        return next;
      });
    },
    [selectedId]
  );

  return (
    <SidebarProvider>
      <AppSidebar
        history={conversations.map(({ id, title }) => ({ id, title }))}
        selectedId={selectedId}
        onSelect={handleSelect}
        onRename={handleRename}
        onDelete={handleDelete}
        onNewChat={handleNewChat}
      />
      <SidebarInset className="bg-sidebar group/sidebar-inset">
        <header className="dark flex h-16 shrink-0 items-center gap-2 px-4 md:px-6 lg:px-8 bg-sidebar text-sidebar-foreground relative before:absolute before:inset-y-3 before:-left-px before:w-px before:bg-gradient-to-b before:from-white/5 before:via-white/15 before:to-white/5 before:z-50">
          <SidebarTrigger className="-ms-2" />
          <div className="flex items-center gap-8 ml-auto">
            <SignedIn>
              <UserButton signOutOptions={{ redirectUrl: '/' }} />
            </SignedIn>
            <SignedOut>
              <SignInButton mode="modal" redirectUrl="/chat" />
            </SignedOut>
          </div>
        </header>
        <div className="flex h-[calc(100svh-4rem)] bg-dark md:rounded-s-3xl md:group-peer-data-[state=collapsed]/sidebar-inset:rounded-s-none transition-all ease-in-out duration-300">
          <Chat
            isNewChat={isNewChat}
            onStartChat={() => setIsNewChat(false)}
            messages={selectedConversation?.messages || []}
            onSend={handleSend}
          />
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
