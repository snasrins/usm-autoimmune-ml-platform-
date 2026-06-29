import { Moon, Palette, Sun, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';
import DashboardLayout from '../components/DashboardLayout';
import { useTheme } from '../contexts/ThemeContext';

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();

  const themeOptions = [
    {
      value: 'light',
      label: 'Light Theme',
      description: 'Bright workspace with cleaner contrast for daytime use.',
      icon: Sun,
      accent: 'from-amber-100 to-orange-100 border-amber-200 text-amber-600'
    },
    {
      value: 'dark',
      label: 'Dark Theme',
      description: 'Low-glare interface with deeper panels for longer sessions.',
      icon: Moon,
      accent: 'from-slate-800 to-purple-900 border-purple-500/30 text-purple-200'
    }
  ];

  return (
    <DashboardLayout>
      <div className="h-[70px] flex items-center gap-8 px-6 bg-white/85 dark:bg-[#0F0F11] border-b border-purple-100 dark:border-white/[0.06] flex-shrink-0 backdrop-blur-md transition-colors">
        <div className="flex flex-col gap-1">
          <h1 className="font-syne text-[18px] font-bold text-[#0F0F11] dark:text-white leading-none">Settings</h1>
          <div className="flex items-center gap-3 text-[12px] text-[#8585A0] dark:text-gray-400">
            <span>USM Autoimmune ML Platform</span>
            <ChevronRight className="w-4 h-4" />
            <span className="text-[#7B5CF0] dark:text-purple-400">Settings</span>
          </div>
        </div>
      </div>

      <main className="flex-1 overflow-y-auto p-6 bg-gradient-to-br from-[#f3f2f8] via-[#f8f7fc] to-[#eeeafb] dark:from-[#181622] dark:via-[#241f35] dark:to-[#1b1827] transition-colors">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="max-w-5xl space-y-6"
        >
          <section className="rounded-2xl border border-purple-100 dark:border-purple-500/20 bg-gradient-to-br from-white via-white to-purple-50/70 dark:from-[#1E1B2E] dark:via-[#221f35] dark:to-[#1E1B2E] p-6 shadow-[0_16px_40px_rgba(88,55,160,0.10)]">
            <div className="flex items-start gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-purple-500 to-indigo-600 shadow-lg shadow-purple-500/30">
                <Palette className="h-6 w-6 text-white" />
              </div>
              <div>
                <h2 className="font-syne text-2xl font-bold text-gray-900 dark:text-white">Appearance</h2>
                <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">Theme controls now live here so the dashboard stays cleaner and focused on data.</p>
              </div>
            </div>
          </section>

          <section className="grid grid-cols-2 gap-5">
            {themeOptions.map((option) => {
              const Icon = option.icon;
              const isActive = theme === option.value;

              return (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setTheme(option.value)}
                  className={`rounded-2xl border p-5 text-left transition-all ${
                    isActive
                      ? 'border-purple-400 bg-white dark:bg-[#211d31] shadow-[0_18px_44px_rgba(88,55,160,0.18)] -translate-y-1'
                      : 'border-purple-100 dark:border-purple-500/20 bg-white/90 dark:bg-[#1E1B2E] shadow-[0_12px_28px_rgba(88,55,160,0.10)] hover:-translate-y-1 hover:shadow-[0_18px_40px_rgba(88,55,160,0.14)]'
                  }`}
                >
                  <div className={`mb-4 flex h-12 w-12 items-center justify-center rounded-2xl border bg-gradient-to-br ${option.accent}`}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{option.label}</h3>
                      <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">{option.description}</p>
                    </div>
                    <div className={`h-4 w-4 rounded-full border-4 ${isActive ? 'border-purple-500 bg-purple-500' : 'border-gray-300 dark:border-gray-600 bg-transparent'}`} />
                  </div>
                </button>
              );
            })}
          </section>

          <section className="rounded-2xl border border-purple-100 dark:border-purple-500/20 bg-white/90 dark:bg-[#1E1B2E] p-6 shadow-[0_14px_34px_rgba(88,55,160,0.10)]">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Current selection</h3>
                <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">The active theme is applied immediately and saved for future sessions.</p>
              </div>
              <span className="rounded-full bg-purple-100 px-4 py-2 text-sm font-semibold text-purple-700 dark:bg-purple-500/20 dark:text-purple-300">
                {theme === 'dark' ? 'Dark mode enabled' : 'Light mode enabled'}
              </span>
            </div>
          </section>
        </motion.div>
      </main>
    </DashboardLayout>
  );
}