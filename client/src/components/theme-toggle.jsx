import { Moon, Sun } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useTheme } from '@/components/theme-provider';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  const handleThemeToggle = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  return (
    <Button
      variant="outline"
      size="icon"
      className="z-50 rounded-full text-primary cursor-pointer"
      onClick={handleThemeToggle}
    >
      {theme === 'dark' ? <Sun /> : <Moon />}
    </Button>
  );
}
