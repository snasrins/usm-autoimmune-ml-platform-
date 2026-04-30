import { AlertTriangle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { motion } from 'framer-motion';

export function DataQualityOverviewPanel({ data, compact = false }) {
  const { missingPercent, classImbalance, outliers, dataSources } = data;
  
  // Sample data for quality trend chart
  const trendData = [
    { name: 'Week 1', value: 75 },
    { name: 'Week 2', value: 82 },
    { name: 'Week 3', value: 78 },
    { name: 'Week 4', value: 88 },
    { name: 'Week 5', value: 91 },
    { name: 'Week 6', value: 94 },
    { name: 'Current', value: 82.2 }
  ];
  
  return (
    <motion.div 
      className={`h-full rounded-3xl ${compact ? 'p-5' : 'p-6'} border transition-all duration-[350ms] ease-out hover:-translate-y-1`}
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
      transition={{ duration: 0.5 }}
    >
      <div className={`flex items-center justify-between ${compact ? 'mb-4' : 'mb-6'}`}>
        <h3 className="text-lg font-bold text-gray-900 dark:text-white tracking-wide">Data Quality Overview</h3>
        <button className="px-4 py-1.5 bg-gray-900 hover:bg-black text-white text-xs font-semibold rounded-lg shadow-sm hover:shadow transition-all">
          View Detailed Report
        </button>
      </div>
      
      {/* Missing Data Section */}
      <div className={compact ? 'mb-4' : 'mb-6'}>
        <div className="flex items-baseline gap-3 mb-2">
          <span className="text-4xl font-bold text-gray-900 dark:text-white">{missingPercent}%</span>
          <span className="text-gray-600 dark:text-gray-400 font-medium">Missing Data</span>
        </div>
        
        <div className="h-2 bg-slate-100 rounded-full overflow-hidden mb-3">
          <div 
            className="h-full rounded-full"
            style={{ width: `${missingPercent}%`, background: 'linear-gradient(to right, #4A1259, #9C27B0, #C2185B)' }}
          />
        </div>
        
        <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
          <span>● 132 outliers</span>
          <span>● 72% / 28% class split</span>
          <span>● 3 data sources</span>
        </div>
      </div>
      
      {/* Quality Trend Chart with Recharts */}
      <div className={compact ? 'mb-4' : 'mb-6'}>
        <div className="relative">
          <div className={compact ? 'mt-0' : 'mt-0'}>
            <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Quality Score Trend</div>
            <ResponsiveContainer width="100%" height={compact ? 120 : 150}>
              <LineChart data={trendData}>
                <defs>
                  <linearGradient id="qualityLineGradient" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#4A1259" />
                    <stop offset="50%" stopColor="#9C27B0" />
                    <stop offset="100%" stopColor="#C2185B" />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" opacity={0.3} />
                <XAxis 
                  dataKey="name" 
                  tick={{ fill: '#9CA3AF', fontSize: 11 }} 
                  stroke="#E5E7EB"
                />
                <YAxis 
                  tick={{ fill: '#9CA3AF', fontSize: 11 }} 
                  stroke="#E5E7EB"
                  domain={[70, 100]}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1F2937', 
                    border: 'none', 
                    borderRadius: '8px',
                    color: '#fff',
                    fontSize: '12px'
                  }}
                />
                <Line 
                  type="monotone" 
                  dataKey="value" 
                  stroke="url(#qualityLineGradient)" 
                  strokeWidth={2.5}
                  dot={{ fill: '#9C27B0', r: 3, strokeWidth: 0 }}
                  activeDot={{ r: 5, fill: '#C2185B', stroke: '#fff', strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
      
      {/* Warning Message */}
      <div className={`flex items-start gap-3 ${compact ? 'p-3' : 'p-4'} bg-yellow-50 dark:bg-yellow-500/10 border border-yellow-200 dark:border-yellow-500/30 rounded-lg`}>
        <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <p className={`${compact ? 'text-xs' : 'text-sm'} text-gray-700 dark:text-gray-200`}>
            High missing values detected in "Autoantibody Levels". 
            <span className="text-purple-600 dark:text-purple-400 font-medium"> Recommendation:</span>
            <span className="text-gray-600 dark:text-gray-300"> Consider running data cleaning</span>
          </p>
        </div>
      </div>
    </motion.div>
  );
}
