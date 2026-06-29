import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import * as Tooltip from '@radix-ui/react-tooltip';

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  
  return (
    <Tooltip.Provider>
      <Tooltip.Root>
        <Tooltip.Trigger asChild>
          <button
            onClick={toggleTheme}
            className="w-8 h-8 rounded-lg bg-gray-100 dark:bg-[#2D2640] border border-gray-200 dark:border-purple-500/20 flex items-center justify-center hover:border-purple-500/50 dark:hover:border-purple-400/50 transition-all group"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-gray-600 dark:text-purple-300 group-hover:text-purple-600 dark:group-hover:text-purple-200 transition-colors" />
            ) : (
              <Moon className="w-4 h-4 text-gray-600 group-hover:text-purple-600 transition-colors" />
            )}
          </button>
        </Tooltip.Trigger>
        <Tooltip.Portal>
          <Tooltip.Content className="px-2.5 py-1.5 bg-gray-900 text-white text-xs rounded shadow-lg" sideOffset={5}>
            {theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            <Tooltip.Arrow className="fill-gray-900" />
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  );
}
