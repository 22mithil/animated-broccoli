import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  RiShining2Line,
  RiAttachment2,
  RiMicLine,
  RiLeafLine,
} from '@remixicon/react';
import { ChatMessage } from '@/components/chat/chat-message';
import { useRef, useEffect, useState, memo } from 'react';
import SiriOrb from './SiriOrb';
import { LoadingMessage } from './loading-animation';
import { ChatService } from '@/services/chat-service';

const orbThemes = {
  // Classic & Professional
  default: {
    bg: 'rgba(102, 126, 234, 0.1)',
    c1: '#667eea',
    c2: '#764ba2',
    c3: '#f093fb',
  },
  ocean: {
    bg: 'rgba(33, 150, 243, 0.05)',
    c1: '#2196f3',
    c2: '#21cbf3',
    c3: '#4fc3f7',
  },
  sunset: {
    bg: 'rgba(255, 154, 158, 0.08)',
    c1: '#ff9a9e',
    c2: '#fad0c4',
    c3: '#ffeaa7',
  },

  // Vibrant & Energetic
  neonCyber: {
    bg: 'rgba(0, 255, 255, 0.05)',
    c1: '#00ffff',
    c2: '#ff00ff',
    c3: '#ffff00',
  },
  electricPurple: {
    bg: 'rgba(118, 75, 162, 0.08)',
    c1: '#764ba2',
    c2: '#a855f7',
    c3: '#ec4899',
  },
  fireGlow: {
    bg: 'rgba(255, 99, 71, 0.06)',
    c1: '#ff6347',
    c2: '#ff4500',
    c3: '#ffd700',
  },

  // Nature Inspired
  forestMint: {
    bg: 'rgba(150, 206, 180, 0.06)',
    c1: '#96ceb4',
    c2: '#85d4c6',
    c3: '#74b9d8',
  },
  aurora: {
    bg: 'rgba(64, 224, 208, 0.05)',
    c1: '#40e0d0',
    c2: '#9370db',
    c3: '#00ff7f',
  },
  deepForest: {
    bg: 'rgba(34, 139, 34, 0.08)',
    c1: '#228b22',
    c2: '#32cd32',
    c3: '#7fffd4',
  },

  // Cosmic & Space
  galaxy: {
    bg: 'rgba(72, 61, 139, 0.08)',
    c1: '#483d8b',
    c2: '#6a5acd',
    c3: '#9370db',
  },
  nebula: {
    bg: 'rgba(138, 43, 226, 0.06)',
    c1: '#8a2be2',
    c2: '#da70d6',
    c3: '#ff1493',
  },
  starlight: {
    bg: 'rgba(25, 25, 112, 0.08)',
    c1: '#191970',
    c2: '#4169e1',
    c3: '#87ceeb',
  },

  // Warm & Cozy
  warmAmber: {
    bg: 'rgba(255, 191, 0, 0.08)',
    c1: '#ffbf00',
    c2: '#ff8c00',
    c3: '#ff6347',
  },
  rosegold: {
    bg: 'rgba(183, 110, 121, 0.08)',
    c1: '#b76e79',
    c2: '#d4af37',
    c3: '#f0e68c',
  },
  coffeeCream: {
    bg: 'rgba(210, 180, 140, 0.08)',
    c1: '#d2b48c',
    c2: '#daa520',
    c3: '#f4a460',
  },

  // Cool & Modern
  iceberg: {
    bg: 'rgba(176, 224, 230, 0.06)',
    c1: '#b0e0e6',
    c2: '#87ceeb',
    c3: '#4682b4',
  },
  arctic: {
    bg: 'rgba(230, 230, 250, 0.08)',
    c1: '#e6e6fa',
    c2: '#b0c4de',
    c3: '#87cefa',
  },
  steel: {
    bg: 'rgba(70, 130, 180, 0.08)',
    c1: '#4682b4',
    c2: '#5f9ea0',
    c3: '#708090',
  },

  // Retro & Vintage
  retroWave: {
    bg: 'rgba(255, 20, 147, 0.08)',
    c1: '#ff1493',
    c2: '#00ced1',
    c3: '#ffd700',
  },
  vaporWave: {
    bg: 'rgba(255, 105, 180, 0.06)',
    c1: '#ff69b4',
    c2: '#00ffff',
    c3: '#ffb6c1',
  },
  synthWave: {
    bg: 'rgba(138, 43, 226, 0.08)',
    c1: '#8a2be2',
    c2: '#ff1493',
    c3: '#00ff00',
  },

  // Monochromatic
  grayscale: {
    bg: 'rgba(128, 128, 128, 0.08)',
    c1: '#808080',
    c2: '#a9a9a9',
    c3: '#d3d3d3',
  },
  blackWhite: {
    bg: 'rgba(0, 0, 0, 0.05)',
    c1: '#000000',
    c2: '#696969',
    c3: '#ffffff',
  },

  // Seasonal
  spring: {
    bg: 'rgba(255, 182, 193, 0.08)',
    c1: '#ffb6c1',
    c2: '#98fb98',
    c3: '#87ceeb',
  },
  summer: {
    bg: 'rgba(255, 215, 0, 0.08)',
    c1: '#ffd700',
    c2: '#ff6347',
    c3: '#32cd32',
  },
  autumn: {
    bg: 'rgba(255, 140, 0, 0.08)',
    c1: '#ff8c00',
    c2: '#dc143c',
    c3: '#b8860b',
  },
  winter: {
    bg: 'rgba(240, 248, 255, 0.08)',
    c1: '#f0f8ff',
    c2: '#b0e0e6',
    c3: '#87ceeb',
  },

  // Gemstone Inspired
  ruby: {
    bg: 'rgba(224, 17, 95, 0.08)',
    c1: '#e01150',
    c2: '#cc0066',
    c3: '#ff1493',
  },
  emerald: {
    bg: 'rgba(80, 200, 120, 0.08)',
    c1: '#50c878',
    c2: '#00ff7f',
    c3: '#32cd32',
  },
  sapphire: {
    bg: 'rgba(15, 82, 186, 0.08)',
    c1: '#0f52ba',
    c2: '#4169e1',
    c3: '#6495ed',
  },
  amethyst: {
    bg: 'rgba(153, 102, 204, 0.08)',
    c1: '#9966cc',
    c2: '#ba55d3',
    c3: '#da70d6',
  },

  // High Contrast
  matrix: {
    bg: 'rgba(0, 0, 0, 0.08)',
    c1: '#00ff00',
    c2: '#32cd32',
    c3: '#7fff00',
  },
  volcano: {
    bg: 'rgba(139, 0, 0, 0.08)',
    c1: '#8b0000',
    c2: '#ff4500',
    c3: '#ffd700',
  },
  electric: {
    bg: 'rgba(0, 0, 139, 0.08)',
    c1: '#00008b',
    c2: '#0000ff',
    c3: '#00bfff',
  },
};

const NewChatView = memo(function NewChatView({
  selectedSize,
  animationDuration,
}) {
  const getRandomTheme = () => {
    const themes = Object.keys(orbThemes);
    const randomTheme = themes[Math.floor(Math.random() * themes.length)];
    return orbThemes[randomTheme];
  };
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[400px] space-y-8 relative z-10">
      <div className="flex justify-center">
        <SiriOrb
          size={selectedSize}
          animationDuration={animationDuration}
          // colors={orbThemes.default}
          colors={getRandomTheme()}
          className="drop-shadow-2xl animate-scale-in"
        />
      </div>
      <div className="text-center space-y-4 max-w-md animate-fade-in">
        <h2 className="text-3xl font-bold text-foreground gradient-text">
          Discover Movies Through Stories
        </h2>
        <p className="text-muted-foreground text-base leading-relaxed">
          Ask me about movies in natural language. Find films by themes,
          characters, emotions, or specific scenes. Try: "Show me movies about
          betrayal" or "Find films that feel like Spirited Away"
        </p>
      </div>
    </div>
  );
});

function ChatMessages({
  isNewChat,
  selectedSize,
  animationDuration,
  messages,
  isLoading,
}) {
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView();
  }, []);

  return isNewChat ? (
    <NewChatView
      selectedSize={selectedSize}
      animationDuration={animationDuration}
    />
  ) : (
    <div className="max-w-3xl mx-auto mt-6 space-y-6 relative z-10">
      {Array.isArray(messages) &&
        messages.map((m) => (
          <ChatMessage key={m.id} isUser={m.role === 'user'}>
            <div className="whitespace-pre-wrap">{m.content}</div>
            {m.role === 'assistant' && m.query_metadata && (
              <div className="mt-2 text-xs text-muted-foreground">
                <p>Query type: {m.query_metadata.detected_label}</p>
                {m.query_metadata.results &&
                  m.query_metadata.results.length > 0 && (
                    <p>
                      Found {m.query_metadata.results.length} relevant results
                    </p>
                  )}
              </div>
            )}
          </ChatMessage>
        ))}
      {isLoading && <LoadingMessage />}
      <div ref={messagesEndRef} aria-hidden="true" />
    </div>
  );
}

function ChatFooter({ inputValue, setInputValue, handleSend, isNewChat }) {
  return (
    <div className="pt-4 pb-4 md:pt-8 md:pb-8 z-50">
      <div className="max-w-3xl mx-auto glass-morphism rounded-2xl animate-slide-up">
        <div className="relative rounded-2xl border border-white/20 dark:border-white/10 bg-muted/30 dark:bg-muted/20 backdrop-blur-sm transition-all duration-300 focus-within:bg-muted/50 dark:focus-within:bg-muted/30 focus-within:border-primary/30 dark:focus-within:border-primary/20 has-[:disabled]:cursor-not-allowed has-[:disabled]:opacity-50 [&:has(input:is(:disabled))_*]:pointer-events-none">
          <textarea
            className="flex sm:min-h-[84px] w-full bg-transparent px-4 py-3 text-[15px] leading-relaxed text-foreground placeholder:text-muted-foreground/70 dark:placeholder:text-muted-foreground/60 focus-visible:outline-none [resize:none]"
            placeholder={
              isNewChat
                ? 'Ask about movies, characters, themes, or scenes...'
                : 'Ask about movies, characters, themes, or scenes...'
            }
            aria-label="Enter your prompt"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
          />
          {/* Textarea buttons */}
          <div className="flex items-center justify-between gap-2 p-3">
            {/* Left buttons */}
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="icon"
                className="rounded-full size-8 border-white/20 dark:border-white/10 hover:bg-white/10 dark:hover:bg-white/5 hover:shadow-md transition-all duration-300 glass-morphism"
              >
                <RiAttachment2
                  className="text-muted-foreground/70 dark:text-muted-foreground/80 size-5"
                  size={20}
                  aria-hidden="true"
                />
                <span className="sr-only">Attach</span>
              </Button>
              <Button
                variant="outline"
                size="icon"
                className="rounded-full size-8 border-white/20 dark:border-white/10 hover:bg-white/10 dark:hover:bg-white/5 hover:shadow-md transition-all duration-300 glass-morphism"
              >
                <RiMicLine
                  className="text-muted-foreground/70 dark:text-muted-foreground/80 size-5"
                  size={20}
                  aria-hidden="true"
                />
                <span className="sr-only">Audio</span>
              </Button>
              <Button
                variant="outline"
                size="icon"
                className="rounded-full size-8 border-white/20 dark:border-white/10 hover:bg-white/10 dark:hover:bg-white/5 hover:shadow-md transition-all duration-300 glass-morphism"
              >
                <RiLeafLine
                  className="text-muted-foreground/70 dark:text-muted-foreground/80 size-5"
                  size={20}
                  aria-hidden="true"
                />
                <span className="sr-only">Action</span>
              </Button>
            </div>
            {/* Right buttons */}
            <div className="flex items-center gap-2">
              <Button
                className="rounded-full h-8 px-6 bg-white/20 dark:bg-white/10 backdrop-blur-sm border border-white/30 dark:border-white/20 text-foreground hover:bg-white/30 dark:hover:bg-white/20 font-medium shadow-lg hover:shadow-xl transition-all duration-300 glass-morphism"
                onClick={handleSend}
                disabled={!inputValue.trim()}
              >
                Find Movies
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Chat({ isNewChat = false, onStartChat, onSend }) {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const selectedSize = '120px';
  const animationDuration = 15;

  useEffect(() => {
    const initializeChat = async () => {
      try {
        const session = await ChatService.createSession();
        setSessionId(session._id);
      } catch (error) {
        console.error('Failed to initialize chat:', error);
      }
    };

    if (isNewChat) {
      initializeChat();
    }
  }, [isNewChat]);

  const handleSend = async () => {
    const trimmed = inputValue.trim();
    if (!trimmed) return;

    if (isNewChat && onStartChat) {
      onStartChat();
    }

    setIsLoading(true);
    setInputValue('');

    try {
      const response = await ChatService.sendMessage(trimmed, sessionId);
      setSessionId(response.sessionId);

      // Update local messages state
      if (response.messages && Array.isArray(response.messages)) {
        setMessages((prevMessages) => [...prevMessages, ...response.messages]);
      }

      // Only notify parent component of new messages if needed
      if (onSend) {
        onSend(response.messages || []);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      // You might want to show an error message to the user here
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ScrollArea className="flex-1 [&>div>div]:h-full w-full md:rounded-s-[inherit] min-[1024px]:rounded-e-3xl bg-transparent relative z-10">
      <div className="h-full flex flex-col px-4 md:px-6 lg:px-8">
        {/* Chat messages area */}
        <div className="relative grow">
          <ChatMessages
            isNewChat={isNewChat}
            selectedSize={selectedSize}
            animationDuration={animationDuration}
            messages={messages}
            isLoading={isLoading}
          />
        </div>
        {/* Footer */}
        <ChatFooter
          inputValue={inputValue}
          setInputValue={setInputValue}
          handleSend={handleSend}
          isNewChat={isNewChat}
        />
      </div>
    </ScrollArea>
  );
}
