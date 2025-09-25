import * as React from 'react';

import { TeamSwitcher } from '@/components/ui/team-switcher';
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
  RiChat1Line,
  RiBardLine,
  RiMickeyLine,
  RiMicLine,
  RiCheckDoubleLine,
  RiBracesLine,
  RiPlanetLine,
  RiSeedlingLine,
  RiSettings3Line,
  RiMore2Fill,
} from '@remixicon/react';

// This is sample data.
const data = {
  history: [
    {
      title: 'Chat',
      url: '#',
      query: 'chat',
      icon: RiChat1Line,
      isActive: true,
    },
    {
      title: 'Real-time',
      url: '#',
      query: 'real-time',
      icon: RiBardLine,
    },
    {
      title: 'Assistants',
      url: '#',
      query: 'assistants',
      icon: RiMickeyLine,
    },
    {
      title: 'Audio',
      url: '#',
      query: 'audio',
      icon: RiMicLine,
    },
    {
      title: 'Metrics',
      url: '#',
      query: 'metrics',
      icon: RiCheckDoubleLine,
    },
    {
      title: 'Documentation',
      url: '#',
      query: 'documentation',
      icon: RiBracesLine,
    },
  ],
};

export function AppSidebar({ ...props }) {
  const handleRename = React.useCallback((item) => {
    console.log('Rename clicked for', item);
    // TODO: wire up rename flow
  }, []);

  const handleDelete = React.useCallback((item) => {
    console.log('Delete clicked for', item);
    // TODO: wire up delete flow
  }, []);

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
              {data.history.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    asChild
                    className="group/menu-button font-medium gap-3 h-9 rounded-md data-[active=true]:hover:bg-transparent data-[active=true]:bg-gradient-to-b data-[active=true]:from-sidebar-primary data-[active=true]:to-sidebar-primary/70 data-[active=true]:shadow-[0_1px_2px_0_rgb(0_0_0/.05),inset_0_1px_0_0_rgb(255_255_255/.12)] [&>svg]:size-auto"
                    isActive={item.isActive}
                  >
                    <a href={item.url}>
                      <span>{item.title}</span>
                    </a>
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
      <SidebarFooter></SidebarFooter>
    </Sidebar>
  );
}
