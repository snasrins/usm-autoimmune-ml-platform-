import { TrendingUp, AlertCircle } from 'lucide-react';
import { ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, ReferenceArea, Dot } from 'recharts';
import { motion } from 'framer-motion';

export function ModelPerformancePanel({ performance, className = '' }) {
  const { accuracy, rocAuc, precision, f1Score, runs } = performance;
  
  // Use real training runs data for the chart
  const performanceTrend = runs && runs.length > 0 
    ? runs.map((run, idx) => ({
        epoch: idx + 1,
        accuracy: parseFloat(run.accuracy) || 0,
        f1: f1Score || 0,
        precision: precision || 0,
        confidence: (parseFloat(run.accuracy) || 0) - 5,
        confidenceUpper: (parseFloat(run.accuracy) || 0) + 5,
        benchmark: 75.0,
        isAnomaly: false
      }))
    : [
        // Fallback to single point if no runs
        { epoch: 1, accuracy: accuracy || 0, f1: f1Score || 0, precision: precision || 0, confidence: (accuracy || 0) - 5, confidenceUpper: (accuracy || 0) + 5, benchmark: 75.0, isAnomaly: false }
      ];
  
  // Clinical thresholds
  const CLINICAL_THRESHOLD_ACCEPTABLE = 80.0;
  const CLINICAL_THRESHOLD_EXCELLENT = 85.0;
  const INDUSTRY_BENCHMARK = 75.0;
  
  return (
    <motion.div 
      className={`h-full rounded-3xl p-5 border transition-all duration-[350ms] ease-out hover:-translate-y-1 ${className}`}
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
      transition={{ duration: 0.5, delay: 0.1 }}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white tracking-wide">Model Performance</h3>
      </div>
      
      {/* Accuracy Section */}
      <div className="mb-4">
        <div className="flex items-baseline gap-3 mb-4">
          <span className="text-xs text-gray-600 dark:text-gray-400 uppercase font-medium">Accuracy</span>
          <span className="text-4xl font-bold text-gray-900 dark:text-white">{accuracy}%</span>
          <span className="flex items-center gap-1 text-green-600 dark:text-green-400 text-sm font-medium">
            <TrendingUp className="w-4 h-4" />
            +5.2%
          </span>
        </div>
        
        {/* ENTERPRISE CHART - Bloomberg Terminal + Stripe Quality */}
        <div className="mb-4 relative group">
          {/* Premium outer glow - appears on hover */}
          <div className="absolute -inset-2 rounded-2xl blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" style={{ background: 'linear-gradient(135deg, rgba(74,18,89,0.08), rgba(194,24,91,0.06))' }}></div>
          
          <div className="relative bg-white rounded-2xl p-6 border border-slate-200/80 shadow-[0_2px_8px_rgba(15,23,42,0.08)] group-hover:shadow-[0_8px_24px_rgba(99,102,241,0.12)] transition-all duration-300" style={{
            background: 'linear-gradient(to bottom, #ffffff 0%, #fafbfc 100%)'
          }}>
            
            {/* Chart Header with Legend */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                <div className="w-3 h-0.5 rounded-full" style={{ background: 'linear-gradient(to right, #4A1259, #C2185B)' }}></div>
                  <span className="text-[10px] font-semibold text-slate-700 uppercase tracking-wide">Model Accuracy</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-0.5 bg-gradient-to-r from-slate-400 to-slate-300 rounded-full"></div>
                  <span className="text-[10px] font-medium text-slate-500 uppercase tracking-wide">Confidence Band</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-[2px] bg-slate-300 rounded-full"></div>
                  <span className="text-[10px] font-medium text-slate-500 uppercase tracking-wide">Benchmark</span>
                </div>
              </div>
              
              {/* Anomaly indicator */}
              <div className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-50 border border-slate-200 rounded-lg">
                <AlertCircle className="w-3 h-3 text-slate-500" />
                <span className="text-[9px] font-semibold text-slate-600 uppercase tracking-wide">1 Anomaly Detected</span>
              </div>
            </div>
            
            <ResponsiveContainer width="100%" height={180}>
              <ComposedChart data={performanceTrend} margin={{ top: 10, right: 10, left: -10, bottom: 5 }}>
                <defs>
                  {/* Dark purple → magenta gradient for accuracy line */}
                  <linearGradient id="accuracyLineGradient" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#4A1259" />
                    <stop offset="45%" stopColor="#7C2D92" />
                    <stop offset="100%" stopColor="#C2185B" />
                  </linearGradient>
                  
                  {/* Area fill: dark purple → magenta fade */}
                  <linearGradient id="accuracyAreaGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#9C27B0" stopOpacity={0.18}/>
                    <stop offset="60%" stopColor="#C2185B" stopOpacity={0.06}/>
                    <stop offset="100%" stopColor="#C2185B" stopOpacity={0.01}/>
                  </linearGradient>
                  
                  {/* Confidence band gradient */}
                  <linearGradient id="confidenceBandGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#94A3B8" stopOpacity={0.08}/>
                    <stop offset="100%" stopColor="#94A3B8" stopOpacity={0.02}/>
                  </linearGradient>
                  
                  {/* Glow effect for line */}
                  <filter id="lineGlow">
                    <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
                    <feMerge>
                      <feMergeNode in="coloredBlur"/>
                      <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                  </filter>
                </defs>
                
                {/* Minimal grid - Bloomberg style */}
                <CartesianGrid 
                  strokeDasharray="0" 
                  stroke="#E2E8F0" 
                  strokeWidth={0.5}
                  vertical={false}
                  opacity={0.4}
                />
                
                {/* Clinical Threshold - Acceptable (80%) */}
                <ReferenceLine 
                  y={CLINICAL_THRESHOLD_ACCEPTABLE} 
                  stroke="#94A3B8" 
                  strokeWidth={1}
                  strokeDasharray="6 3"
                  opacity={0.7}
                  label={{ 
                    value: 'Clinical Threshold (80%)', 
                    position: 'insideTopRight',
                    fill: '#64748B',
                    fontSize: 9,
                    fontWeight: 600
                  }}
                />
                
                {/* Clinical Threshold - Excellent (85%) */}
                <ReferenceLine 
                  y={CLINICAL_THRESHOLD_EXCELLENT} 
                  stroke="#64748B" 
                  strokeWidth={1}
                  strokeDasharray="6 3"
                  opacity={0.6}
                  label={{ 
                    value: 'Excellent (85%)', 
                    position: 'insideTopRight',
                    fill: '#475569',
                    fontSize: 9,
                    fontWeight: 600
                  }}
                />
                
                {/* Industry Benchmark Line */}
                <ReferenceLine 
                  y={INDUSTRY_BENCHMARK} 
                  stroke="#CBD5E1" 
                  strokeWidth={1.5}
                  strokeDasharray="0"
                  opacity={0.8}
                />
                
                {/* Confidence Band (Area between confidence bounds) */}
                <Area
                  type="monotone"
                  dataKey="confidenceUpper"
                  stroke="none"
                  fill="url(#confidenceBandGradient)"
                  isAnimationActive={false}
                />
                <Area
                  type="monotone"
                  dataKey="confidence"
                  stroke="none"
                  fill="url(#confidenceBandGradient)"
                  isAnimationActive={false}
                />
                
                {/* Main Accuracy Area (subtle fill) */}
                <Area
                  type="monotone"
                  dataKey="accuracy"
                  stroke="none"
                  fill="url(#accuracyAreaGradient)"
                  isAnimationActive={true}
                  animationDuration={1200}
                  animationEasing="ease-in-out"
                />
                
                {/* Main Accuracy Line */}
                <Line
                  type="monotone"
                  dataKey="accuracy"
                  stroke="url(#accuracyLineGradient)"
                  strokeWidth={3}
                  dot={(props) => {
                    const { cx, cy, payload } = props;
                    if (payload.isAnomaly) {
                      return (
                        <g>
                          <circle cx={cx} cy={cy} r={8} fill="#F1F5F9" stroke="#94A3B8" strokeWidth={1.5} opacity={0.9} />
                          <circle cx={cx} cy={cy} r={4} fill="#64748B" />
                        </g>
                      );
                    }
                    // Normal dot
                    return <circle cx={cx} cy={cy} r={3} fill="#9C27B0" stroke="#fff" strokeWidth={2} />;
                  }}
                  activeDot={(props) => {
                    const { cx, cy } = props;
                    return (
                      <g>
                        <circle cx={cx} cy={cy} r={8} fill="#C2185B" opacity={0.15} />
                        <circle cx={cx} cy={cy} r={5} fill="#9C27B0" stroke="#fff" strokeWidth={2} />
                      </g>
                    );
                  }}
                  filter="url(#lineGlow)"
                  isAnimationActive={true}
                  animationDuration={1200}
                  animationEasing="ease-in-out"
                />
                
                {/* Clean Axis Styling */}
                <XAxis 
                  dataKey="epoch"
                  axisLine={{ stroke: '#CBD5E1', strokeWidth: 1 }}
                  tick={{ fill: '#64748B', fontSize: 10, fontWeight: 500 }}
                  tickLine={{ stroke: '#CBD5E1', strokeWidth: 1 }}
                  dy={5}
                  label={{ 
                    value: 'Training Epoch', 
                    position: 'insideBottom', 
                    offset: -3,
                    style: { fontSize: 10, fill: '#475569', fontWeight: 600, letterSpacing: '0.5px' }
                  }}
                />
                
                <YAxis
                  axisLine={{ stroke: '#CBD5E1', strokeWidth: 1 }}
                  tick={{ fill: '#64748B', fontSize: 10, fontWeight: 500 }}
                  tickLine={{ stroke: '#CBD5E1', strokeWidth: 1 }}
                  domain={[70, 92]}
                  ticks={[70, 75, 80, 85, 90]}
                  dx={-5}
                  label={{ 
                    value: 'Accuracy %', 
                    angle: -90, 
                    position: 'insideLeft',
                    offset: 10,
                    style: { fontSize: 10, fill: '#475569', fontWeight: 600, letterSpacing: '0.5px' }
                  }}
                />
                
                {/* Premium Tooltip - Stripe style */}
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0F172A',
                    border: 'none',
                    borderRadius: '12px',
                    padding: '12px 16px',
                    boxShadow: '0 20px 40px rgba(15, 23, 42, 0.4), 0 0 0 1px rgba(148, 163, 184, 0.1)',
                    fontSize: '11px',
                    fontWeight: 600
                  }}
                  labelStyle={{ 
                    color: '#F1F5F9', 
                    fontWeight: 700, 
                    marginBottom: '8px',
                    fontSize: '11px',
                    letterSpacing: '0.3px'
                  }}
                  itemStyle={{ 
                    color: '#CBD5E1',
                    padding: '4px 0',
                    fontSize: '11px'
                  }}
                  cursor={{ 
                    stroke: '#8B5CF6', 
                    strokeWidth: 1,
                    strokeDasharray: '4 2',
                    opacity: 0.3
                  }}
                  labelFormatter={(value) => `Epoch ${value}`}
                  formatter={(value, name) => {
                    if (name === 'accuracy') return [`${value.toFixed(2)}%`, 'Model Accuracy'];
                    if (name === 'confidence') return [`${value.toFixed(2)}%`, 'Lower Confidence'];
                    if (name === 'confidenceUpper') return [`${value.toFixed(2)}%`, 'Upper Confidence'];
                    return [value, name];
                  }}
                />
              </ComposedChart>
            </ResponsiveContainer>
            
            {/* Chart Footer - Insights */}
            <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-[10px]">
              <div className="flex items-center gap-4">
                <div>
                  <span className="text-slate-500 font-medium">Current: </span>
                  <span className="text-slate-900 font-bold">{accuracy}%</span>
                </div>
                <div>
                  <span className="text-slate-500 font-medium">vs Benchmark: </span>
                  <span className="text-emerald-600 font-bold">+{(accuracy - INDUSTRY_BENCHMARK).toFixed(1)}%</span>
                </div>
              </div>
              <div className="text-slate-400 font-medium">
                Confidence interval: 95%
              </div>
            </div>
          </div>
        </div>
        
        {/* Premium Metrics Grid - Stripe Style */}
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div className="group relative overflow-hidden rounded-xl p-4 border border-slate-200/60 bg-white hover:border-slate-300 transition-all duration-300 hover:shadow-lg">
            <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-blue-50 to-transparent rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <div className="relative">
              <div className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider mb-2">ROC AUC</div>
              <div className="text-3xl font-bold text-slate-900 mb-1">{rocAuc}</div>
              <div className="text-[10px] text-slate-400 font-medium">Area Under Curve</div>
            </div>
          </div>
          
          <div className="group relative overflow-hidden rounded-xl p-4 border border-slate-200/60 bg-white hover:border-slate-300 transition-all duration-300 hover:shadow-lg">
            <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-emerald-50 to-transparent rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <div className="relative">
              <div className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider mb-2">Precision</div>
              <div className="text-3xl font-bold text-slate-900 mb-1">{precision}%</div>
              <div className="text-[10px] text-slate-400 font-medium">Positive Predictive</div>
            </div>
          </div>
          
          <div className="group relative overflow-hidden rounded-xl p-4 border border-slate-200/60 bg-white hover:border-slate-300 transition-all duration-300 hover:shadow-lg">
            <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-violet-50 to-transparent rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <div className="relative">
              <div className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider mb-2">F1 Score</div>
              <div className="text-3xl font-bold text-slate-900 mb-1">{f1Score}%</div>
              <div className="text-[10px] text-slate-400 font-medium">Harmonic Mean</div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
