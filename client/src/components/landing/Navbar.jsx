import {
  Navbar,
  NavBody,
  NavItems,
  MobileNav,
  NavbarLogo,
  NavbarButton,
  MobileNavHeader,
  MobileNavToggle,
  MobileNavMenu,
} from '../ui/resizable-navbar'; // adjust import path
import { useState } from 'react';
import {
  SignedIn,
  SignedOut,
  SignInButton,
  SignUpButton,
  UserButton,
} from '@clerk/clerk-react';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from '@/components/theme-toggle';

export function LandingNavbar() {
  const navItems = [
    { name: 'How It Works', link: '/how-it-works' },
    { name: 'Features', link: '/#features' },
    { name: 'Demo', link: '/demo' },
    { name: 'About', link: '/about' },
  ];

  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <Navbar className="z-[150]">
      <NavBody>
        <NavbarLogo />
        <NavItems items={navItems} />
        <div className="flex items-center gap-4">
          {/* Theme Toggle */}
          <ThemeToggle />
          {/* Authentication buttons */}
          <SignedOut>
            <SignInButton mode="modal" redirectUrl="/chat">
              <Button variant="outline" size="sm">
                Sign In
              </Button>
            </SignInButton>
            <SignUpButton mode="modal" redirectUrl="/chat">
              <Button size="sm">Sign Up</Button>
            </SignUpButton>
          </SignedOut>
          <SignedIn>
            <UserButton signOutOptions={{ redirectUrl: '/' }} />
          </SignedIn>
        </div>
      </NavBody>

      {/* Mobile Navigation */}
      <MobileNav>
        <MobileNavHeader>
          <NavbarLogo />
          <div className="flex items-center gap-4">
            <ThemeToggle />
            <MobileNavToggle
              isOpen={isMobileMenuOpen}
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            />
          </div>
        </MobileNavHeader>

        <MobileNavMenu
          isOpen={isMobileMenuOpen}
          onClose={() => setIsMobileMenuOpen(false)}
        >
          {navItems.map((item, idx) => (
            <a
              key={`mobile-link-${idx}`}
              href={item.link}
              onClick={() => setIsMobileMenuOpen(false)}
              className="relative text-neutral-600 dark:text-neutral-300"
            >
              <span className="block">{item.name}</span>
            </a>
          ))}
          <div className="flex w-full flex-col gap-4">
            {/* Mobile Authentication buttons */}
            <SignedOut>
              <SignInButton mode="modal" redirectUrl="/chat">
                <Button variant="outline" className="w-full">
                  Sign In
                </Button>
              </SignInButton>
              <SignUpButton mode="modal" redirectUrl="/chat">
                <Button className="w-full">Sign Up</Button>
              </SignUpButton>
            </SignedOut>
            <SignedIn>
              <div className="flex items-center justify-center">
                <UserButton signOutOptions={{ redirectUrl: '/' }} />
              </div>
            </SignedIn>
          </div>
        </MobileNavMenu>
      </MobileNav>
    </Navbar>
  );
}
