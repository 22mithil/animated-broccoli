import { Button } from '@/components/ui/button';
import { Route, Routes } from 'react-router';
import Landing from './pages/landing/Landing';
import ChatLayout from './pages/chat/ChatLayout';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/chat" element={<ChatLayout />} />
    </Routes>
  );
}

export default App;
