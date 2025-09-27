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
import { ThemeToggle } from '@/components/theme-toggle';

export default function ChatLayout() {
  const [conversations, setConversations] = useState([
    {
      id: 'sample-1',
      title: 'Movie Discovery',
      messages: [
        {
          id: 'm1',
          role: 'user',
          content: 'Show me movies about betrayal and redemption',
        },
        {
          id: 'm2',
          role: 'assistant',
          content:
            'I found several movies that explore themes of betrayal and redemption. "The Shawshank Redemption" follows Andy Dufresne\'s journey from wrongful imprisonment to redemption. "Casino" shows the betrayal and eventual redemption of Sam Rothstein. "The Godfather Part II" explores Michael Corleone\'s moral descent and attempts at redemption. Would you like me to find more specific examples or explore similar themes?',
        },
        {
          id: 'm3',
          role: 'user',
          content: 'What about movies that feel like Spirited Away?',
        },
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
    const newConv = { id, title: 'New Movie Search', messages: [] };
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
          content:
            'I found some relevant movies in our knowledge graph. Let me search for more specific information about your query.',
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
        <header className="glass-morphism flex h-16 shrink-0 items-center gap-2 px-4 md:px-6 lg:px-8 text-sidebar-foreground relative border-b border-white/10 dark:border-white/5">
          <SidebarTrigger className="-ms-2" />
          <div className="flex items-center gap-4 ml-auto">
            <ThemeToggle />
            <SignedIn>
              <UserButton signOutOptions={{ redirectUrl: '/' }} />
            </SignedIn>
            <SignedOut>
              <SignInButton mode="modal" redirectUrl="/chat" />
            </SignedOut>
          </div>
        </header>
        <div className="flex h-[calc(100svh-4rem)] bg-background md:rounded-s-3xl md:group-peer-data-[state=collapsed]/sidebar-inset:rounded-s-none transition-all ease-in-out duration-300 relative overflow-hidden">
          {/* Background gradient similar to landing page */}
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary/10 blur-3xl" />
          <div className="absolute inset-0 bg-gradient-to-t from-background/80 via-transparent to-background/60" />
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
