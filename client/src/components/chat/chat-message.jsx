import { cn } from '@/lib/utils';
import {
  TooltipProvider,
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  RiCodeSSlashLine,
  RiBookLine,
  RiLoopRightFill,
  RiCheckLine,
} from '@remixicon/react';

export function ChatMessage({ isUser, children }) {
  return (
    <article
      className={cn(
        'flex items-start gap-4 text-[15px] leading-relaxed',
        isUser && 'justify-end'
      )}
    >
      <img
        className={cn(
          'rounded-full',
          isUser ? 'order-1' : 'border border-black/[0.08] shadow-sm'
        )}
        src={
          isUser
            ? 'https://raw.githubusercontent.com/origin-space/origin-images/refs/heads/main/exp2/user-02_mlqqqt.png'
            : 'https://raw.githubusercontent.com/origin-space/origin-images/refs/heads/main/exp2/user-01_i5l7tp.png'
        }
        alt={isUser ? 'User profile' : 'Bart logo'}
        width={40}
        height={40}
      />
      <div
        className={cn(isUser ? 'bg-muted px-4 py-3 rounded-xl' : 'space-y-4')}
      >
        <div className="flex flex-col gap-3">
          <p className="sr-only">{isUser ? 'You' : 'Bart'} said:</p>
          {children}
        </div>
      </div>
    </article>
  );
}