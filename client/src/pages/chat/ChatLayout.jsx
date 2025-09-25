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
  return (
    <SidebarProvider>
      <AppSidebar />
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
          <Chat />
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
