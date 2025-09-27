import React from 'react';

export function LoadingAnimation() {
  return (
    <div className="flex items-center space-x-2 animate-pulse">
      <div className="w-2 h-2 rounded-full bg-primary/60"></div>
      <div className="w-2 h-2 rounded-full bg-primary/60 animation-delay-200"></div>
      <div className="w-2 h-2 rounded-full bg-primary/60 animation-delay-400"></div>
    </div>
  );
}

export function LoadingMessage() {
  return (
    <div className="flex items-start space-x-4 animate-fade-in">
      <div className="size-8 rounded-full bg-primary/20 flex items-center justify-center">
        <div className="size-4 rounded-full bg-primary/40"></div>
      </div>
      <div className="flex-1 space-y-2 py-1">
        <div className="h-4 bg-primary/20 rounded w-3/4"></div>
        <div className="space-y-2">
          <div className="h-4 bg-primary/10 rounded"></div>
          <div className="h-4 bg-primary/10 rounded w-5/6"></div>
        </div>
      </div>
    </div>
  );
}
