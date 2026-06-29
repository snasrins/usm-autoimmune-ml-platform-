import { Rocket, BarChart3, Building2, LineChart, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

export function SystemInsightsPanel() {
  const navigate = useNavigate();

  const quickActions = [
    {
      label: 'Start New Workflow',
      description: 'Navigate to Data Ingestion',
      path: '/data-ingestion',
      icon: Rocket
    },
    {
      label: 'View Model Performance',
      description: 'Navigate to Model Comparison',
      path: '/model-comparison',
      icon: BarChart3
    },
    {
      label: 'Score New Patients',
      description: 'Navigate to Batch Prediction',
      path: '/batch-prediction',
      icon: Building2
    },
    {
      label: 'Analyze Data',
      description: 'Navigate to EDA',
      path: '/eda',
      icon: LineChart
    }
  ];
  
  return (
    <div className="space-y-4">
      {/* Quick Actions Panel - Glass Effect */}
      <motion.div 
        className="relative overflow-hidden rounded-3xl p-5 border sticky top-4 transition-all duration-[350ms] ease-out hover:-translate-y-1"
        style={{
          background: 'rgba(255, 255, 255, 0.72)',
          backdropFilter: 'blur(18px)',
          WebkitBackdropFilter: 'blur(18px)',
          border: '1px solid rgba(255, 255, 255, 0.6)',
          boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.7), 0 8px 32px rgba(15, 23, 42, 0.05)'
        }}
        whileHover={{
          boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.7), 0 18px 50px rgba(15, 23, 42, 0.08)'
        }}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        <div className="flex items-center gap-2 mb-4">
          <div className="w-8 h-8 rounded-lg bg-purple-600 flex items-center justify-center">
            <Rocket className="w-4 h-4 text-white" />
          </div>
          <h3 className="text-lg font-bold text-gray-900 tracking-wide">Quick Actions</h3>
        </div>
        
        <div className="space-y-2.5">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <button
                key={action.path}
                onClick={() => navigate(action.path)}
                className="w-full flex items-center gap-3 p-3 bg-white hover:bg-purple-50 border border-purple-200/50 hover:border-purple-300 rounded-xl shadow-sm hover:shadow transition-all group"
              >
                <div className="w-9 h-9 rounded-lg bg-purple-100 flex items-center justify-center flex-shrink-0">
                  <Icon className="w-4.5 h-4.5 text-purple-600" />
                </div>
                <div className="flex-1 text-left min-w-0">
                  <div className="text-sm font-medium text-gray-900">
                    {action.label}
                  </div>
                  <div className="text-xs text-gray-600 truncate">
                    {action.description}
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-purple-600 flex-shrink-0 transition-colors" />
              </button>
            );
          })}
        </div>
      </motion.div>
    </div>
  );
}

export function GPUUsageSummaryCard({ gpuUsage, compact = false, className = '' }) {
  const size = compact ? 84 : 96;
  const radius = compact ? 36 : 42;
  const circumference = 2 * Math.PI * radius;
  const loadState = gpuUsage.percentage >= 80 ? 'High Load' : gpuUsage.percentage >= 60 ? 'Moderate Load' : 'Low Load';

  return (
    <motion.div 
      className={`relative overflow-hidden h-full bg-gradient-to-br from-white via-indigo-50/60 to-purple-100/70 dark:from-[#1E1B2E] dark:via-[#25203A] dark:to-[#1E1B2E] rounded-2xl ${compact ? 'p-4' : 'p-5'} border border-indigo-200 dark:border-purple-500/30 shadow-[0_16px_40px_rgba(62,80,210,0.16)] hover:shadow-[0_24px_56px_rgba(88,55,160,0.24)] transition-colors ${className}`}
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, delay: 0.5 }}
      whileHover={{ scale: 1.02 }}
    >
      <div className="absolute -left-10 -top-8 h-28 w-28 rounded-full bg-cyan-400/20 blur-2xl pointer-events-none" />
      <div className="absolute -right-10 bottom-0 h-28 w-28 rounded-full bg-fuchsia-500/20 blur-2xl pointer-events-none" />

      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white">GPU Usage</h3>
        <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${gpuUsage.percentage >= 80 ? 'bg-rose-100 text-rose-700' : gpuUsage.percentage >= 60 ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'} dark:bg-white/10 dark:text-white`}>
          {loadState}
        </span>
      </div>

      <div className={`flex ${compact ? 'items-center gap-3' : 'items-center gap-4'} mb-4`}>
        <div className="relative" style={{ width: `${size}px`, height: `${size}px` }}>
          <svg className="transform -rotate-90" width={size} height={size}>
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              className="stroke-indigo-100 dark:stroke-[#2D2640]"
              strokeWidth={compact ? 9 : 10}
              fill="none"
            />
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              stroke="url(#gpuGradientSummary)"
              strokeWidth={compact ? 9 : 10}
              fill="none"
              strokeDasharray={`${(gpuUsage.percentage / 100) * circumference} ${circumference}`}
              strokeLinecap="round"
            />
            <defs>
              <linearGradient id="gpuGradientSummary" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#06B6D4" />
                <stop offset="55%" stopColor="#8B5CF6" />
                <stop offset="100%" stopColor="#D946EF" />
              </linearGradient>
            </defs>
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className={`${compact ? 'text-2xl' : 'text-3xl'} font-bold text-gray-900 dark:text-white drop-shadow-[0_0_10px_rgba(124,58,237,0.25)]`}>{gpuUsage.percentage}%</span>
          </div>
        </div>

        <div>
          <div className="text-gray-900 dark:text-white font-bold text-lg">{gpuUsage.used} / {gpuUsage.total}</div>
          <div className="text-xs text-indigo-700 dark:text-indigo-300 font-semibold">hours used</div>
        </div>
      </div>

      <div className="space-y-2 text-xs text-gray-600 dark:text-gray-300">
        <div className="flex items-center justify-between">
          <span>Weekly Allowance: 8 hours</span>
        </div>
        <div className="flex items-center justify-between">
          <span>Reset in 10d 5m</span>
        </div>
      </div>
    </motion.div>
  );
}
