import { motion } from 'framer-motion';

// Fallback mock data shown when API returns no features
const MOCK_FEATURES = [
  { name: 'ANA Level',        value: 87 },
  { name: 'Anti-dsDNA',       value: 74 },
  { name: 'ESR',              value: 61 },
  { name: 'Age',              value: 53 },
  { name: 'C3 Complement',    value: 44 },
  { name: 'CRP',              value: 38 },
  { name: 'Gender',           value: 27 },
  { name: 'Disease Duration', value: 19 },
];

// Dark purple → magenta progression
const BAR_COLORS = [
  { bar: '#4A1259', bg: 'rgba(74,18,89,0.08)',    light: false },
  { bar: '#6A1478', bg: 'rgba(106,20,120,0.08)',   light: false },
  { bar: '#7B1FA2', bg: 'rgba(123,31,162,0.08)',   light: false },
  { bar: '#9C27B0', bg: 'rgba(156,39,176,0.07)',   light: false },
  { bar: '#AD1457', bg: 'rgba(173,20,87,0.07)',    light: false },
  { bar: '#C2185B', bg: 'rgba(194,24,91,0.07)',    light: false },
  { bar: '#D81B60', bg: 'rgba(216,27,96,0.06)',    light: true  },
  { bar: '#E91E8C', bg: 'rgba(233,30,140,0.06)',   light: true  },
];

export function FeatureImportancePanel({ features, compact = false, className = '' }) {
  // Use API data if available, otherwise fall back to mock
  const rawData = features && features.length > 0
    ? features.map(f => ({ name: f.name, value: Math.round(Math.abs(parseFloat(f.score)) * 100) }))
    : MOCK_FEATURES;

  // Sort descending, cap at 8 items
  const chartData = [...rawData].sort((a, b) => b.value - a.value).slice(0, 8);
  const maxVal = chartData[0]?.value || 100;

  return (
    <motion.div 
      className={`relative overflow-hidden rounded-3xl ${compact ? 'p-5 flex flex-col h-full' : 'p-6'} border transition-all duration-[350ms] ease-out hover:-translate-y-1 ${className}`}
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
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
    >
      {/* Header */}
      <div className="relative flex items-center justify-between mb-4 flex-shrink-0">
        <div>
          <h3 className="text-lg font-bold text-gray-900 tracking-wide">Feature Importance</h3>
          <p className="text-[10px] text-slate-400 font-medium mt-0.5 uppercase tracking-wide">Top predictive biomarkers</p>
        </div>
        <button className="px-3 py-1 text-xs text-purple-600 hover:text-purple-700 font-semibold transition-colors">
          View All
        </button>
      </div>

      {/* Custom horizontal bar list — spreads to fill card */}
      <div className={`${compact ? 'flex-1 flex flex-col justify-between' : 'space-y-2.5'} pr-1`}>
        {chartData.map((item, index) => {
          const color = BAR_COLORS[index % BAR_COLORS.length];
          const pct = Math.round((item.value / maxVal) * 100);
          return (
            <motion.div
              key={item.name}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, delay: index * 0.06 }}
            >
              {/* Label row */}
              <div className="flex items-center justify-between mb-1">
                <span className="text-[11px] font-semibold text-slate-700 truncate max-w-[160px]">{item.name}</span>
                <span className="text-[11px] font-bold ml-2 flex-shrink-0" style={{ color: color.bar }}>{item.value}%</span>
              </div>
              {/* Bar track */}
              <div className="relative h-5 rounded-full overflow-hidden" style={{ background: color.bg }}>
                <motion.div
                  className="absolute left-0 top-0 h-full rounded-full"
                  style={{ background: color.bar }}
                  initial={{ width: 0 }}
                  animate={{ width: `${pct}%` }}
                  transition={{ duration: 0.7, delay: index * 0.06, ease: 'easeOut' }}
                />
                {/* Rank badge */}
                <div className="absolute right-2 top-0 h-full flex items-center">
                  <span className="text-[9px] font-bold text-white/70">#{index + 1}</span>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
      
      {/* Model Info */}
      <div className={`relative text-xs text-gray-600 dark:text-gray-300 space-y-1 border-t border-gray-200 dark:border-purple-500/20 ${compact ? 'pt-3 p-2.5' : 'pt-4 p-3'} bg-gray-50 dark:bg-[#2D2640]/35 rounded-lg`}>
        <div className="flex justify-between">
          <span>Model Trained:</span>
          <span className="font-semibold text-gray-800 dark:text-gray-200">1 hour ago</span>
        </div>
        <div className="flex justify-between">
          <span>Dataset:</span>
          <span className="font-semibold text-gray-800 dark:text-gray-200">Imbalanced Data v2.6</span>
        </div>
        <div className="flex justify-between">
          <span>Model:</span>
          <span className="font-semibold text-gray-800 dark:text-gray-200">Hybrid Ensemble V2.8</span>
        </div>
      </div>
      
      {/* View All Button */}
      <button className={`w-full ${compact ? 'mt-3 py-2' : 'mt-6 py-2.5'} px-4 bg-gray-900 hover:bg-black text-white text-sm font-semibold rounded-lg shadow-sm hover:shadow transition-all`}>
        View All Experiments
      </button>
    </motion.div>
  );
}
