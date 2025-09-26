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
import {
  RiMore2Fill,
  RiAddLine,
} from '@remixicon/react';

export function AppSidebar({
  history = [],
  selectedId,
  onSelect,
  onRename,
  onDelete,
  onNewChat,
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
    <Sidebar {...props} className="dark !border-none">
      <SidebarHeader className="text-2xl font-extrabold tracking-wide">
        LOGO
      </SidebarHeader>
      <SidebarContent>
        {/* We only show the first parent group */}
        <SidebarGroup>
          <SidebarGroupLabel className="uppercase text-sidebar-foreground/50">
            History
          </SidebarGroupLabel>
          <SidebarGroupContent className="px-2">
            <SidebarMenu>
              {history.map((item) => (
                <SidebarMenuItem key={item.id || item.title}>
                  <SidebarMenuButton
                    asChild
                    className="group/menu-button font-medium gap-3 h-9 rounded-md data-[active=true]:hover:bg-transparent data-[active=true]:bg-gradient-to-b data-[active=true]:from-sidebar-primary data-[active=true]:to-sidebar-primary/70 data-[active=true]:shadow-[0_1px_2px_0_rgb(0_0_0/.05),inset_0_1px_0_0_rgb(255_255_255/.12)] [&>svg]:size-auto"
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
                      <SidebarMenuAction aria-label="Item actions" showOnHover>
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
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              className="group/menu-button font-medium gap-3 h-9 rounded-md hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
            >
              <button
                className="flex items-center gap-3 w-full"
                onClick={handleNewChatClick}
              >
                <RiAddLine size={16} />
                <span>New Chat</span>
              </button>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
