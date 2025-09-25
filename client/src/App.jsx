import { Route, Routes } from 'react-router-dom';
import {
  RedirectToSignIn,
  SignedIn,
  SignedOut,
  SignIn,
  SignUp,
} from '@clerk/clerk-react';
import Landing from './pages/landing/Landing';
import ChatLayout from './pages/chat/ChatLayout';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route
        path="/chat"
        element={
          <>
            <SignedIn>
              <ChatLayout />
            </SignedIn>
            <SignedOut>
              <RedirectToSignIn />
            </SignedOut>
          </>
        }
      />
      <Route
        path="/sign-in/*"
        element={
          <SignIn routing="path" path="/sign-in" afterSignInUrl="/chat" />
        }
      />
      <Route
        path="/sign-up/*"
        element={
          <SignUp routing="path" path="/sign-up" afterSignUpUrl="/chat" />
        }
      />
    </Routes>
  );
}

export default App;
