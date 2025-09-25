import React from 'react';
import {
  SignedIn,
  SignedOut,
  SignInButton,
  SignUpButton,
  UserButton,
} from '@clerk/clerk-react';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';

function Landing() {
  return (
    <div className="min-h-svh flex flex-col items-center justify-center gap-6 p-6">
      <h1 className="text-3xl font-bold">Welcome</h1>
      <p className="text-muted-foreground">Sign in to start chatting.</p>
      <div className="flex items-center gap-3">
        <SignedOut>
          <SignInButton mode="modal" redirectUrl="/chat">
            <Button>Sign in</Button>
          </SignInButton>
          <SignUpButton mode="modal" redirectUrl="/chat">
            <Button variant="outline">Sign up</Button>
          </SignUpButton>
        </SignedOut>
        <SignedIn>
          <Link to="/chat">
            <Button>Go to Chat</Button>
          </Link>
          <UserButton signOutOptions={{ redirectUrl: '/' }} />
        </SignedIn>
      </div>
    </div>
  );
}

export default Landing;
