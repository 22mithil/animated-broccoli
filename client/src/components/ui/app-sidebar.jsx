import * as React from 'react';

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuAction,
  SidebarMenuItem,
} from '@/components/ui/sidebar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { RiMore2Fill, RiAddLine } from '@remixicon/react';
import { NavbarLogo } from './resizable-navbar';

export function AppSidebar({
  history = [],
  selectedId,
  onSelect,
  onRename,
  onDelete,
  onNewChat,
  isLoading = false,
  ...props
}) {
  const handleRename = React.useCallback(
    (item) => {
      if (onRename) onRename(item);
    },
    [onRename]
  );

  const handleDelete = React.useCallback(
    (item) => {
      if (onDelete) onDelete(item);
    },
    [onDelete]
  );

  const handleNewChatClick = React.useCallback(() => {
    if (onNewChat) {
      onNewChat();
    }
  }, [onNewChat]);

  return (
    <Sidebar {...props} className="dark !border-none glass-morphism">
      <SidebarHeader className="flex items-start justify-center text-2xl font-extrabold tracking-wide gradient-text">
        <NavbarLogo />
      </SidebarHeader>
      <SidebarContent>
        {/* We only show the first parent group */}
        <SidebarGroup>
          <SidebarGroupLabel className="uppercase text-sidebar-foreground/50">
            Search History
          </SidebarGroupLabel>
          <SidebarGroupContent className="px-2">
            <SidebarMenu>
              {isLoading ? (
                <div className="flex flex-col gap-2 px-2 py-1">
                  <div className="h-8 w-full animate-pulse rounded-md bg-white/5"></div>
                  <div className="h-8 w-full animate-pulse rounded-md bg-white/5"></div>
                  <div className="h-8 w-full animate-pulse rounded-md bg-white/5"></div>
                </div>
              ) : history.length === 0 ? (
                <div className="flex flex-col items-center justify-center gap-2 py-8 text-center text-sm text-sidebar-foreground/50">
                  <p>No chat history yet</p>
                  <button
                    onClick={onNewChat}
                    className="text-primary hover:text-primary/80 transition-colors"
                  >
                    Start a new chat
                  </button>
                </div>
              ) : (
                history.map((item) => (
                  <SidebarMenuItem key={item.id || item.title}>
                    <SidebarMenuButton
                      asChild
                      className="group/menu-button font-medium gap-3 h-9 rounded-md data-[active=true]:hover:bg-transparent data-[active=true]:bg-gradient-to-b data-[active=true]:from-sidebar-primary data-[active=true]:to-sidebar-primary/70 data-[active=true]:shadow-[0_1px_2px_0_rgb(0_0_0/.05),inset_0_1px_0_0_rgb(255_255_255/.12)] [&>svg]:size-auto hover:bg-white/5 transition-all duration-300"
                      isActive={
                        (item.id && item.id === selectedId) || item.isActive
                      }
                    >
                      <button
                        type="button"
                        className="w-full text-left"
                        onClick={() => onSelect && onSelect(item)}
                      >
                        <span>{item.title}</span>
                      </button>
                    </SidebarMenuButton>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <SidebarMenuAction
                          aria-label="Item actions"
                          showOnHover
                        >
                          <RiMore2Fill size={16} aria-hidden="true" />
                        </SidebarMenuAction>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="start" sideOffset={6}>
                        <DropdownMenuItem onSelect={() => handleRename(item)}>
                          Rename
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          variant="destructive"
                          onSelect={() => handleDelete(item)}
                        >
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </SidebarMenuItem>
                ))
              )}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              className="group/menu-button font-medium gap-3 h-9 rounded-md hover:bg-white/5 hover:text-sidebar-accent-foreground transition-all duration-300 glass-morphism"
            >
              <button
                className="flex items-center gap-3 w-full"
                onClick={handleNewChatClick}
              >
                <RiAddLine size={16} />
                <span>New Search</span>
              </button>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
